import pandas as pd
import os

# Define path to your dataset
path = "C:/Users/MSI/Desktop/Book Sphere/data"

# Load CSV
books = pd.read_csv(f"{path}/books_cleaned.csv")

# Check first rows
print(books.head())
