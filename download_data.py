import pandas as pd

url = "https://huggingface.co/datasets/nitesh/CreditCardFraudDetection/resolve/main/creditcard.csv"
print(f"Downloading from {url}...")
df = pd.read_csv(url)
print(f"Downloaded shape: {df.shape}")
df.to_csv("d:/Razorpay/ai-payment-risk-manager/data/raw/creditcard.csv", index=False)
print("Saved to data/raw/creditcard.csv")
