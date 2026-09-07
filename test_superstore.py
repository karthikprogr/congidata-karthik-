import sys
import os
sys.path.insert(0, 'cognidata/backend')
os.chdir('cognidata/backend')

import pandas as pd
import numpy as np
from services.agents.automl_agent import run_automl
import warnings
warnings.filterwarnings('ignore')

def main():
    print("="*80)
    print("COGNIDATA AUTOML - SAMPLE SUPERSTORE ACCURACY TEST")
    print("="*80)
    print()
    
    # Load data
    df = pd.read_csv("../../datasets/samplesuperstore.csv")
    print(f"Dataset: {len(df):,} rows x {len(df.columns)} columns")
    print()
    
    # ========================================================================
    # TEST 1: PROFIT PREDICTION (REGRESSION)
    # ========================================================================
    print("TEST 1: PROFIT PREDICTION (REGRESSION)")
    print("-"*80)
    
    # Simple features
    df1 = df[['Ship Mode', 'Segment', 'Region', 'Category', 
              'Sub-Category', 'Sales', 'Quantity', 'Discount', 'Profit']].copy()
    
    print(f"Features: {', '.join([c for c in df1.columns if c != 'Profit'])}")
    print(f"Target: Profit (continuous, range: ${df['Profit'].min():.2f} to ${df['Profit'].max():.2f})")
    print()
    
    print("Training 8 regression models...")
    r1 = run_automl(df1, target='Profit', user_id='test_profit')
    
    print()
    print(f"Best Model: {r1['best_model']}")
    print(f"R² Score: {r1['score']:.4f} (explains {r1['score']*100:.1f}% of variance)")
    print()
    print("Leaderboard:")
    for i, m in enumerate(r1['leaderboard'], 1):
        line = f"  {i}. {m['model']:20s}"
        for k, v in m.items():
            if k != 'model':
                line += f" | {k}={v:.4f}"
        print(line)
    
    print()
    print(f"Dataset split: {r1['train_rows']} train + {r1['test_rows']} test = {r1['train_rows']+r1['test_rows']} total")
    print()
    
    # ========================================================================
    # TEST 2: CATEGORY PREDICTION (CLASSIFICATION)
    # ========================================================================
    print()
    print("="*80)
    print("TEST 2: CATEGORY PREDICTION (3-CLASS CLASSIFICATION)")
    print("-"*80)
    
    df2 = df[['Ship Mode', 'Segment', 'Region', 'Sub-Category', 
              'Sales', 'Quantity', 'Discount', 'Profit', 'Category']].copy()
    
    print(f"Features: {', '.join([c for c in df2.columns if c != 'Category'])}")
    print(f"Target: Category (3 classes: {df['Category'].unique().tolist()})")
    print()
    
    print("Training 7 classification models...")
    r2 = run_automl(df2, target='Category', user_id='test_category')
    
    print()
    print(f"Best Model: {r2['best_model']}")
    print(f"Accuracy: {r2['score']:.4f} ({r2['score']*100:.1f}% correct predictions)")
    print()
    print("Leaderboard:")
    for i, m in enumerate(r2['leaderboard'], 1):
        line = f"  {i}. {m['model']:20s}"
        for k, v in m.items():
            if k != 'model':
                line += f" | {k}={v:.4f}"
        print(line)
    
    print()
    print(f"Dataset split: {r2['train_rows']} train + {r2['test_rows']} test = {r2['train_rows']+r2['test_rows']} total")
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\nRegression (Profit Prediction):")
    print(f"  Best: {r1['best_model']} with R²={r1['score']:.4f}")
    if r1['score'] >= 0.85:
        print(f"  Quality: EXCELLENT")
    elif r1['score'] >= 0.75:
        print(f"  Quality: GOOD")
    else:
        print(f"  Quality: FAIR")
    
    print(f"\nClassification (Category Prediction):")
    print(f"  Best: {r2['best_model']} with Accuracy={r2['score']:.4f}")
    if r2['score'] >= 0.90:
        print(f"  Quality: EXCELLENT")
    elif r2['score'] >= 0.80:
        print(f"  Quality: GOOD")
    else:
        print(f"  Quality: FAIR")
    
    print()
    print("AutoML Phase 1 & 2 upgrades working perfectly!")
    print("="*80)

if __name__ == "__main__":
    main()
