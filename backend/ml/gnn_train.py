import os
import json
import random
import torch
import torch.nn.functional as F
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch_geometric.loader import DataLoader
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt

from backend.ml.gnn_model import FraudGAT, SubgraphDataset

def generate_synthetic_data(num_subgraphs=1000):
    subgraphs = []
    for _ in range(num_subgraphs):
        is_fraud_subgraph = random.random() < 0.1
        num_nodes = random.randint(3, 10)
        nodes = []
        for i in range(num_nodes):
            is_fraud_node = 1 if (is_fraud_subgraph and random.random() < 0.5) else 0
            features = {
                "account_age_normalised": random.random(),
                "kyc_tier": random.choice([0, 1, 2, 3]) / 3.0,
                "historical_avg_amount_log": random.uniform(2, 6),
                "velocity_24h": random.random() if not is_fraud_node else random.uniform(0.5, 1.0),
                "velocity_7d": random.random(),
                "counterparty_entropy": random.uniform(0, 4),
                "inbound_ratio": random.random(),
                "deviation_from_baseline": random.uniform(0, 1) if not is_fraud_node else random.uniform(0.5, 1.0),
                "is_dormant": random.choice([0, 1]),
                "kyc_update_pending": random.choice([0, 1]),
                "pep_adjacent": random.choice([0, 1]),
                "account_type_encoded": random.choice([0.0, 0.5, 1.0]),
            }
            nodes.append({"account_id": f"ACC-{i}", "features": features, "is_fraud": is_fraud_node})
        
        edges = []
        for _ in range(num_nodes * 2):
            src, tgt = random.sample(range(num_nodes), 2)
            edge_features = {
                "amount_ratio": random.random() if not is_fraud_subgraph else random.uniform(0.8, 1.0),
                "time_since_last_txn_normalised": random.random(),
                "channel_encoded": random.choice([0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
                "is_new_counterparty": random.choice([0, 1]),
                "amount_log_normalised": random.random(),
                "same_branch": random.choice([0, 1]),
            }
            edges.append({"source": f"ACC-{src}", "target": f"ACC-{tgt}", "features": edge_features})
            
        subgraphs.append({"nodes": nodes, "edges": edges})
    return subgraphs

def train():
    print("Loading data...")
    os.makedirs('data/synthetic', exist_ok=True)
    data_path = 'data/synthetic/transactions.json'
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            raw_data = json.load(f)
    else:
        print("No existing data found, generating synthetic dataset...")
        raw_data = generate_synthetic_data(2000)
        with open(data_path, 'w') as f:
            json.dump(raw_data, f)
            
    fraud_graphs = []
    normal_graphs = []
    for g in raw_data:
        has_fraud = any(n.get("is_fraud", 0) == 1 for n in g.get("nodes", []))
        if has_fraud:
            fraud_graphs.append(g)
        else:
            normal_graphs.append(g)
            
    oversampled_data = normal_graphs.copy()
    for _ in range(8):
        for fg in fraud_graphs:
            noisy_fg = {"nodes": [], "edges": fg["edges"]}
            for n in fg["nodes"]:
                nf = n["features"].copy()
                nf["velocity_24h"] = min(1.0, max(0.0, nf["velocity_24h"] + random.uniform(-0.05, 0.05)))
                noisy_fg["nodes"].append({"account_id": n["account_id"], "features": nf, "is_fraud": n.get("is_fraud", 0)})
            oversampled_data.append(noisy_fg)
            
    random.shuffle(oversampled_data)
    
    n = len(oversampled_data)
    train_data = oversampled_data[:int(0.7*n)]
    val_data = oversampled_data[int(0.7*n):int(0.85*n)]
    test_data = oversampled_data[int(0.85*n):]
    
    train_ds = SubgraphDataset(train_data)
    val_ds = SubgraphDataset(val_data)
    test_ds = SubgraphDataset(test_data)
    
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)
    test_loader = DataLoader(test_ds, batch_size=64)
    
    model = FraudGAT()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([2.0]).to(device))
    
    epochs = 100
    patience = 15
    best_val_f1 = 0
    patience_counter = 0
    
    history = {"train_loss": [], "val_loss": [], "val_f1": []}
    
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            _, out = model(batch.x, batch.edge_index, batch.edge_attr)
            loss = criterion(out.squeeze(), batch.y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        train_loss /= len(train_loader)
        
        model.eval()
        val_loss = 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                _, out = model(batch.x, batch.edge_index, batch.edge_attr)
                loss = criterion(out.squeeze(), batch.y)
                val_loss += loss.item()
                
                probs = torch.sigmoid(out).squeeze().cpu().numpy()
                if probs.ndim == 0:
                    probs = torch.tensor([probs])
                
                all_preds.extend((probs > 0.70).astype(int).tolist())
                all_labels.extend(batch.y.cpu().numpy().tolist())
                
        val_loss /= len(val_loader)
        val_f1 = f1_score(all_labels, all_preds, zero_division=0)
        
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_f1"].append(val_f1)
        
        scheduler.step(val_f1)
        
        print(f"Epoch {epoch+1:03d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f}")
        
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            os.makedirs('models', exist_ok=True)
            torch.save(model.state_dict(), 'models/gnn_v1.pt')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered.")
                break
                
    # Test Evaluation
    model.load_state_dict(torch.load('models/gnn_v1.pt'))
    model.eval()
    all_probs, all_preds, all_labels = [], [], []
    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            _, out = model(batch.x, batch.edge_index, batch.edge_attr)
            probs = torch.sigmoid(out).squeeze().cpu().numpy()
            
            if probs.ndim == 0:
                probs = torch.tensor([probs])
                
            all_preds.extend((probs > 0.70).astype(int).tolist())
            all_probs.extend(probs.tolist())
            all_labels.extend(batch.y.cpu().numpy().tolist())
            
    test_prec = precision_score(all_labels, all_preds, zero_division=0)
    test_rec = recall_score(all_labels, all_preds, zero_division=0)
    test_f1 = f1_score(all_labels, all_preds, zero_division=0)
    
    try:
        test_auc = roc_auc_score(all_labels, all_probs)
        tn, fp, fn, tp = confusion_matrix(all_labels, all_preds).ravel()
        test_fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    except Exception:
        test_auc = 0
        test_fpr = 0
        
    print(f"\nFinal Test Metrics:")
    print(f"Precision: {test_prec:.4f}")
    print(f"Recall: {test_rec:.4f}")
    print(f"F1 Score: {test_f1:.4f}")
    print(f"FPR: {test_fpr:.4f}")
    print(f"AUC-ROC: {test_auc:.4f}")
    
    report = {
        "test_precision": test_prec,
        "test_recall": test_rec,
        "test_f1": test_f1,
        "test_fpr": test_fpr,
        "test_auc": test_auc,
        "history": history
    }
    with open('training_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train')
    plt.plot(history['val_loss'], label='Val')
    plt.title('Loss')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(history['val_f1'], label='Val F1', color='green')
    plt.title('F1 Score')
    plt.legend()
    plt.savefig('training_curves.png')
    print("Saved models/gnn_v1.pt, training_report.json, and training_curves.png")

if __name__ == "__main__":
    train()
