import sys
sys.path.insert(0, r"d:\Cognidata_mainfinal-main\cognidata\backend")

from services.agents import automl_agent
import pandas as pd
import numpy as np

print("="*70)
print("PHASE 1 FINAL VERIFICATION TEST")
print("="*70)

print("\n[TEST 1] Model Registry")
reg = list(automl_agent.REGRESSION_MODELS.keys())
cls = list(automl_agent.CLASSIFICATION_MODELS.keys())
print(f"Regression ({len(reg)}): {reg}")
print(f"Classification ({len(cls)}): {cls}")

print("\n[TEST 2] Live Training")
np.random.seed(42)
df = pd.DataFrame({"a": np.random.rand(50), "b": np.random.rand(50), "y": np.random.rand(50)})
result = automl_agent.run_automl(df, "y", "test")
print(f"Best: {result['best_model']}")
print(f"Score: {result['score']:.4f}")
print(f"Models trained: {len(result['leaderboard'])}")

print("\n[TEST 3] Prediction")
pred = automl_agent.predict("test", {"a": 0.5, "b": 0.5})
print(f"Prediction works: {'prediction' in pred}")

print("\n" + "="*70)
if len(reg) == 8 and len(cls) == 7:
    print("PHASE 1: SUCCESSFULLY IMPLEMENTED ?")
else:
    print("PHASE 1: INCOMPLETE")
print("="*70)
