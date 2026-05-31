import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch.nn import BatchNorm1d, Linear
from torch_geometric.data import Data, Dataset

class SubgraphDataset(Dataset):
    def __init__(self, subgraphs):
        """
        subgraphs: list of dicts, each dict like:
        {
            "nodes": [
                {"account_id": "ACC-0041", "features": {...}, "is_fraud": 1 or 0 (optional)}
            ],
            "edges": [
                {"source": "ACC-...", "target": "ACC-...", "features": {...}}
            ]
        }
        """
        super().__init__()
        self.subgraphs = subgraphs

    def len(self):
        return len(self.subgraphs)

    def get(self, idx):
        subgraph = self.subgraphs[idx]
        return self.process_subgraph(subgraph)

    @staticmethod
    def process_subgraph(subgraph):
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        # Map node ids to indices
        node_idx_map = {n["account_id"]: i for i, n in enumerate(nodes)}

        # Extract node features
        node_features = []
        node_labels = []
        for n in nodes:
            f = n.get("features", {})
            node_feat = [
                float(f.get("account_age_normalised", 0.0)),
                float(f.get("kyc_tier", 0.0)),
                float(f.get("historical_avg_amount_log", 0.0)),
                float(f.get("velocity_24h", 0.0)),
                float(f.get("velocity_7d", 0.0)),
                float(f.get("counterparty_entropy", 0.0)),
                float(f.get("inbound_ratio", 0.0)),
                float(f.get("deviation_from_baseline", 0.0)),
                float(f.get("is_dormant", 0.0)),
                float(f.get("kyc_update_pending", 0.0)),
                float(f.get("pep_adjacent", 0.0)),
                float(f.get("account_type_encoded", 0.0)),
            ]
            node_features.append(node_feat)
            node_labels.append(float(n.get("is_fraud", 0.0)))
        
        x = torch.tensor(node_features, dtype=torch.float)
        y = torch.tensor(node_labels, dtype=torch.float)

        # Extract edge features
        edge_index_list = []
        edge_attr_list = []
        for e in edges:
            src = node_idx_map.get(e["source"])
            tgt = node_idx_map.get(e["target"])
            if src is None or tgt is None:
                continue
            
            f = e.get("features", {})
            edge_feat = [
                float(f.get("amount_ratio", 0.0)),
                float(f.get("time_since_last_txn_normalised", 0.0)),
                float(f.get("channel_encoded", 0.0)),
                float(f.get("is_new_counterparty", 0.0)),
                float(f.get("amount_log_normalised", 0.0)),
                float(f.get("same_branch", 0.0)),
            ]
            edge_index_list.append([src, tgt])
            edge_attr_list.append(edge_feat)
        
        if len(edge_index_list) > 0:
            edge_index = torch.tensor(edge_index_list, dtype=torch.long).t().contiguous()
            edge_attr = torch.tensor(edge_attr_list, dtype=torch.float)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 6), dtype=torch.float)
            
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
        data.node_ids = [n["account_id"] for n in nodes]
        return data


class FraudGAT(torch.nn.Module):
    def __init__(self, in_channels=12, edge_dim=6, hidden_channels=64, out_channels=1, heads=4, dropout=0.3):
        super(FraudGAT, self).__init__()
        self.dropout = dropout
        
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads, edge_dim=edge_dim, concat=True)
        self.bn1 = BatchNorm1d(hidden_channels * heads)
        
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=heads, edge_dim=edge_dim, concat=True)
        self.bn2 = BatchNorm1d(hidden_channels * heads)
        
        self.conv3 = GATConv(hidden_channels * heads, hidden_channels, heads=heads, edge_dim=edge_dim, concat=False)
        self.bn3 = BatchNorm1d(hidden_channels)
        
        self.lin = Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index, edge_attr):
        x = self.conv1(x, edge_index, edge_attr=edge_attr)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.conv2(x, edge_index, edge_attr=edge_attr)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.conv3(x, edge_index, edge_attr=edge_attr)
        if x.size(0) > 1:
            x = self.bn3(x)
        embeddings = F.relu(x)
        embeddings = F.dropout(embeddings, p=self.dropout, training=self.training)
        
        out = self.lin(embeddings)
        return embeddings, out

    def predict_subgraph(self, nodes, edges):
        self.eval()
        subgraph = {"nodes": nodes, "edges": edges}
        data = SubgraphDataset.process_subgraph(subgraph)
        
        device = next(self.parameters()).device
        data.x = data.x.to(device)
        data.edge_index = data.edge_index.to(device)
        data.edge_attr = data.edge_attr.to(device)
        
        with torch.no_grad():
            embeddings, logits = self.forward(data.x, data.edge_index, data.edge_attr)
            probs = torch.sigmoid(logits).squeeze(-1).tolist()
            
            if not isinstance(probs, list):
                probs = [probs]
                
            result = {}
            for account_id, prob in zip(data.node_ids, probs):
                result[account_id] = prob
                
            return result
