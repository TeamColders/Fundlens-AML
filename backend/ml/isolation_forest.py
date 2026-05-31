import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

class PeerGroupAnomalyScorer:
    def __init__(self, contamination=0.05, random_state=42):
        self.model = IsolationForest(
            contamination=contamination, 
            random_state=random_state,
            n_estimators=100
        )
        self.is_fitted = False

    def train(self, X: np.ndarray):
        """
        Trains the Isolation Forest on historical node features.
        X should be a numpy array of shape (n_samples, n_features)
        """
        self.model.fit(X)
        self.is_fitted = True

    def score(self, X: np.ndarray) -> np.ndarray:
        """
        Returns anomaly scores for new samples.
        The sklearn decision_function returns positive for inliers and negative for outliers.
        We invert and scale this so 0 = normal, 1 = highly anomalous.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")
        
        # decision_function: anomaly score of X of the base classifiers.
        # The anomaly score of the input samples is computed as
        # the mean anomaly score of the trees in the forest.
        # The measure of normality of an observation given a tree is the depth
        # of the leaf containing this observation, which is equivalent to
        # the number of splittings required to isolate this point.
        # Inliers tend to have positive scores, outliers negative.
        scores = self.model.decision_function(X)
        
        # Invert and normalize linearly to [0, 1] for typical ranges
        # Typically scores are between -0.5 and +0.5
        # Lower score = more anomalous. We want higher output = more anomalous
        normalized = 0.5 - (scores / 2.0)
        return np.clip(normalized, 0.0, 1.0)

    def save(self, path: str):
        joblib.dump(self.model, path)

    def load(self, path: str):
        self.model = joblib.load(path)
        self.is_fitted = True

# Example Usage
if __name__ == "__main__":
    # Generate random dummy data representing 100 normal accounts (12 features)
    X_train = np.random.randn(100, 12) * 0.1
    
    # Train the scorer
    scorer = PeerGroupAnomalyScorer()
    scorer.train(X_train)
    
    # Test with a normal and an anomalous sample
    X_test_normal = np.random.randn(1, 12) * 0.1
    X_test_anomaly = np.random.randn(1, 12) * 2.0 + 1.0 # Shifted mean and higher variance
    
    score_normal = scorer.score(X_test_normal)[0]
    score_anomaly = scorer.score(X_test_anomaly)[0]
    
    print(f"Normal Account Anomaly Score: {score_normal:.4f}")
    print(f"Anomalous Account Anomaly Score: {score_anomaly:.4f}")
