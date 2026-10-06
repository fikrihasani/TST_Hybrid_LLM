import pandas as pd

df =pd.read_csv("data/combined_stif.csv")

print(df.columns)

print(df.head())

print(df["formality"].value_counts())
