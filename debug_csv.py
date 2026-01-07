import pandas as pd
import os

FILENAME = "Roof-by-Sarayut-LRFD-V.1.0.3.xlsx - Data Steel.csv"

def inspect():
    if not os.path.exists(FILENAME):
        print("File not found.")
        return

    print("--- Reading raw (header=0, nrows=5) ---")
    try:
        df_raw = pd.read_csv(FILENAME, header=None, nrows=5)
        print(df_raw)
    except Exception as e:
        print(e)
        
    print("\n--- Reading header=2 (expected) ---")
    try:
        df = pd.read_csv(FILENAME, header=2)
        print("Columns:", df.columns.tolist())
        
        # Check mapping logic
        rename_map = {}
        for col in df.columns:
            c = str(col).lower().strip() # Added str() and strip() for safety
            if 'section' in c: rename_map[col] = 'Section'
            elif 'weight' in c: rename_map[col] = 'Weight'
            elif 'ix' in c: rename_map[col] = 'Ix'
            elif 'zx' in c: rename_map[col] = 'Zx'
            elif 'area' in c: rename_map[col] = 'Area'
            elif c == 'h': rename_map[col] = 'h'
            elif c == 't': rename_map[col] = 't'
            
        print("\nMap matches:", rename_map)
        
        df_renamed = df.rename(columns=rename_map)
        print("Renamed Columns:", df_renamed.columns.tolist())
        
        if 'Section' in df_renamed.columns:
            print("Section column FOUND.")
        else:
            print("Section column MISSING.")
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    inspect()
