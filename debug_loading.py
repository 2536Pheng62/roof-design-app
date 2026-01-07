from data_utils import load_data, DEFAULT_FILENAME
import pandas as pd
import os

print(f"Current CWD: {os.getcwd()}")
print(f"Testing load_data with {DEFAULT_FILENAME}")

if os.path.exists(DEFAULT_FILENAME):
    print(f"File exists. Size: {os.path.getsize(DEFAULT_FILENAME)} bytes")
    with open(DEFAULT_FILENAME, 'r', encoding='utf-8') as f:
        print(f"First line: {f.readline()}")
else:
    print("File does not exist!")

try:
    df = load_data(DEFAULT_FILENAME)
    print("Result DataFrame:")
    print(df)
    if df.empty:
        print("DataFrame is empty.")
    else:
        print("Columns:", df.columns.tolist())
except Exception as e:
    print(f"Exception calling load_data: {e}")
