import csv
import re

input_file = "tables_dump.txt"
output_csv = "tis_1228_steel.csv"

# Regex to match H x A x C (e.g., 60 x 30 x 10 or 100 x 50 x 20)
dim_pattern = re.compile(r"(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)")

data_rows = []

current_h = None
current_a = None
current_c = None

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

is_target_table = False
idx_map = {'Dimensions': 0, 't': 1, 'Area': 2, 'Weight': 3, 'Ix': 6, 'Zx': 10}

for line in lines:
    # Check for header row and update map
    if "Zx" in line and "Ix" in line:
        try:
            header_row = eval(line.strip())
            idx_map = {}
            for i, col in enumerate(header_row):
                c = str(col).strip()
                if 'H' in c and 'x' in c: idx_map['Dimensions'] = i
                elif c == 't': idx_map['t'] = i
                elif c == 'a' or 'Area' in c: idx_map['Area'] = i 
                elif 'Iy' in c: idx_map['Iy'] = i 
                elif c == 'Ix': idx_map['Ix'] = i
                elif c == 'Zx': idx_map['Zx'] = i
                
            if 'Area' not in idx_map: idx_map['Area'] = 2
            if 'Weight' not in idx_map: idx_map['Weight'] = 3
        except:
            pass
        # Do not continue, let it trigger table start below if applicable

    # Check for start of data table
    if "H × A × C" in line or "H x A x C" in line:
        is_target_table = True
        continue
    
    if "Table" in line and "Found" in line:
        is_target_table = False
        
    if not is_target_table:
        continue
        
    # Process Row
    try:
        if not line.strip().startswith("["):
            continue
            
        row = eval(line.strip())
        if len(row) < 10: continue
            
        # Extract using map
        if 'Dimensions' not in idx_map or 'Zx' not in idx_map:
            col0_idx = 0
            zx_idx = 10
        else:
            col0_idx = idx_map['Dimensions']
            zx_idx = idx_map['Zx']
            
        col0 = row[col0_idx].strip()
        
        def get_val(key, default_idx):
            idx = idx_map.get(key, default_idx)
            if idx < len(row):
                return row[idx].strip()
            return "0"

        t_str = get_val('t', 1)
        area_str = get_val('Area', 2)
        weight_str = get_val('Weight', 3)
        ix_str = get_val('Ix', 6)
        zx_str = row[zx_idx].strip()
        
        if col0 == "" or col0 == "''":
            if current_h is None: continue 
        else:
            match = dim_pattern.search(col0)
            if match:
                current_h = match.group(1)
                current_a = match.group(2)
                current_c = match.group(3)
            else:
                continue
                
        def clean_num(s):
            return s.replace(' ', '').replace(',', '')
            
        h = int(current_h)
        section_name = f"C-{current_h}x{current_a}x{current_c}x{t_str}"
        
        # Avoid duplicates or invalid rows?
        # Just process all
        
        weight = float(clean_num(weight_str))
        ix = float(clean_num(ix_str))
        zx = float(clean_num(zx_str))
        area = float(clean_num(area_str))
        t = float(clean_num(t_str))
        
        data_rows.append([section_name, weight, ix, zx, area, h, t])
        
    except Exception as e:
        pass

# Write CSV
# Deduplicate based on Section Name
unique_data = {}
for row in data_rows:
    unique_data[row[0]] = row

final_rows = list(unique_data.values())

header = ["Section", "Weight", "Ix", "Zx", "Area", "h", "t"]
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(final_rows)

print(f"Generated {output_csv} with {len(final_rows)} rows.")
