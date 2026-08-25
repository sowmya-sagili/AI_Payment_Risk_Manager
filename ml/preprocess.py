import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer

def inspect_dataset(df):
    print("--- Dataset Inspection ---")
    print(f"Number of rows: {df.shape[0]}")
    print(f"Number of columns: {df.shape[1]}")
    print(f"Column names: {df.columns.tolist()}")
    print(f"Data types:\n{df.dtypes}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print(f"Duplicate records: {df.duplicated().sum()}")
    print(f"Target distribution (Class):\n{df['Class'].value_counts(normalize=True)}")
    
    num_features = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_features = df.select_dtypes(include=['object', 'category']).columns.tolist()
    print(f"Numerical features: {len(num_features)}")
    print(f"Categorical features: {len(cat_features)}")

def load_and_preprocess(raw_data_path="data/raw/creditcard.csv"):
    print(f"Loading data from {raw_data_path}...")
    df = pd.read_csv(raw_data_path)
    
    inspect_dataset(df)
    
    # Remove duplicates
    if df.duplicated().sum() > 0:
        print("Dropping duplicates...")
        df = df.drop_duplicates()
        
    X = df.drop(columns=['Class'])
    y = df['Class'].astype(int)
    
    # Feature Engineering
    print("Performing feature engineering...")
    # Time-based features: The 'Time' feature contains the seconds elapsed between each transaction and the first transaction.
    # We can derive the hour of the day to capture diurnal patterns in fraud.
    if 'Time' in X.columns:
        X['HourOfDay'] = (X['Time'] // 3600) % 24
        X = X.drop(columns=['Time'])
    else:
        # Fallback if dataset lacks Time
        X['HourOfDay'] = 0
    
    # Amount deviation: Fraudulent transactions often have extreme amounts. Log transform helps with skewness.
    if 'Amount' in X.columns:
        X['LogAmount'] = np.log1p(X['Amount'])

    
    return X, y

def get_preprocessor():
    """
    Creates a scikit-learn preprocessing pipeline.
    Uses RobustScaler to handle outliers common in transaction amounts and PCA features.
    """
    preprocessor = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler())
    ])
    return preprocessor
