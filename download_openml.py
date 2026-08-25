import pandas as pd
from sklearn.datasets import fetch_openml
import os
import urllib.request
import ssl

print("Downloading creditcard dataset from OpenML...")
# Bypass SSL cert verification just in case
ssl._create_default_https_context = ssl._create_unverified_context

# The creditcard dataset ID on openml is 1597. We can also fetch by name.
try:
    dataset = fetch_openml(name='creditcard', version=1, as_frame=True, parser='auto')
    df = dataset.frame
    df.to_csv("data/raw/creditcard.csv", index=False)
    print("Successfully saved to data/raw/creditcard.csv")
except Exception as e:
    print(f"Error: {e}")
