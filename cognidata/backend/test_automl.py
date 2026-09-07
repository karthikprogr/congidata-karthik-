import sys
sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from services.agents.automl_agent import run_automl
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("COGNIDATA AUTOML ACCURACY TEST - SAMPLE SUPERSTORE")
print("=" * 80)

# Load dataset
df = pd.read_csv("../../datasets/samplesuperstore.csv")
print(f"Loaded: {len(df)} rows, {len(df.columns)} columns\n")

# TEST 1: PREDICT PROFIT (REGRESSION)
print("=" * 80)
print("TEST 1: PREDICT PROFIT (REGRESSION)")
print("=" * 80)

# Prepare data - simple features only
df_test = df[['Ship Mode', 'Segment', 'Region', 'Category', 
              'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit']].copy()

print(f"Features: {list(df_test.columns)}")
print(f"Target: Profit\n")

print("Training AutoML models...")
result = run_automl(df_test, target='Profit', user_id='test1')

print("\nRESULTS:")
print(f"  Best Model: {result['best_model']}")
print(f"  Score (R²): {result['score']:.4f}")
print(f"\n  Leaderboard:")
for i, m in enumerate(result['leaderboard'][:5], 1):
    metrics = ', '.join([f"{k}={v:.4f}" for k,v in m.items() if k!='model'])
    print(f"    {i}. {m['model']:20s} {metrics}")

print(f"\n  Train/Test: {result['train_rows']}/{result['test_rows']} rows")

# Quality assessment
r2 = result['score']
if r2 >= 0.85:
    print(f"\n  Quality: EXCELLENT (explains {r2*100:.1f}% of variance)")
elif r2 >= 0.75:
    print(f"\n  Quality: GOOD (explains {r2*100:.1f}% of variance)")
else:
    print(f"\n  Quality: FAIR (explains {r2*100:.1f}% of variance)")

