import pandas as pd

df = pd.read_csv("data/combined_stif.csv")
print(f"Jumlah data: {len(df)}")
print("Distribusi label:")
print(df['formality'].value_counts())
