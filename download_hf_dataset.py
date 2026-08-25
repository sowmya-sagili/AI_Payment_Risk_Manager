import os
import pandas as pd
from datasets import load_dataset

def main():
    print("Downloading dataset from HuggingFace...")
    # 'jyunyilin/credit-card-fraud-detection' is a popular one for the classic Kaggle dataset
    dataset = load_dataset("jyunyilin/credit-card-fraud-detection")
    
    df = dataset["train"].to_pandas()
    
    out_dir = "data/raw"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "creditcard.csv")
    
    df.to_csv(out_path, index=False)
    print(f"Dataset saved to {out_path} with shape {df.shape}")

if __name__ == "__main__":
    main()
