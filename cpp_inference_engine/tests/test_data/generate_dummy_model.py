import lightgbm as lgb
import numpy as np
from pathlib import Path

# Simulate 100 rows with 27 features (to match FeatureMatrixRow)
X = np.random.rand(100, 27).astype(np.float32)
y = np.random.randint(0, 2, size=100)  # Binary classification

train_data = lgb.Dataset(X, label=y)

params = {"objective": "binary", "metric": "binary_logloss", "verbosity": -1}

# Resolve script directory
script_dir = Path(__file__).resolve().parent
model_path = script_dir / "lgbm_model.txt"

model = lgb.train(params, train_data, num_boost_round=10)
model.save_model(model_path)
