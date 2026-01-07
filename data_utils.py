import pandas as pd
import os

REQUIRED_COLUMNS = {
    'Section': 'Section',
    'Weight': 'Weight',
    'Ix': 'Ix',
    'Zx': 'Zx',
    'Area': 'A',
    'h': 'h',
    't': 't'
}

DEFAULT_FILENAME = "tis_1228_steel.csv"

def create_dummy_csv(filepath):
    """Creates a dummy CSV file with sample data if the file is missing."""
    data = {
        'Section': ['C-100x50x20x3.2', 'C-125x50x20x3.2', 'C-150x50x20x3.2', 'C-75x45x15x2.3'],
        'Weight': [5.5, 6.13, 6.76, 3.25], # kg/m
        'Ix': [78.6, 128.0, 192.0, 31.5], # cm4
        'Zx': [15.7, 20.5, 25.6, 8.4], # cm3
        'A': [7.01, 7.81, 8.61, 4.14], # cm2
        'h': [100, 125, 150, 75], # mm
        't': [3.2, 3.2, 3.2, 2.3] # mm
    }
    
    # Create the structure with blank rows to mimic the complex header mentioned
    # Row 1, 2 are skip rows. Header is at row 3 (index 2).
    
    # We will just create a clean CSV for simplicity since we control the dummy generation,
    # BUT the reader must handle the skipping. 
    # To be safe and compliant with the prompt's description of "complex structure",
    # let's write it in a standard pandas way but the reader will need to be robust.
    # Actually, let's create it 'clean' for the dummy, but the reader will use 'header=0' for the dummy
    # or we can verify if the prompt *requires* us to mimic the bad structure.
    # "The CSV structure is complex (headers start at row 3, index 2)."
    
    # Let's try to mimic it to be robust.
    df = pd.DataFrame(data)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        f.write("Metadata Row 1\n")
        f.write("Metadata Row 2\n")
        df.to_csv(f, index=False)
        
    return df

def load_data(filepath=DEFAULT_FILENAME):
    """Loads and cleans the CSV data with robust header detection."""
    if not os.path.exists(filepath):
        print(f"File {filepath} not found. Creating dummy file.")
        create_dummy_csv(filepath)
    
    try:
        # Pre-scan the file to find the header row
        header_row_idx = -1
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line_lower = line.lower()
                if 'section' in line_lower and 'weight' in line_lower:
                    header_row_idx = i
                    break
        
        if header_row_idx == -1:
            # Fallback: maintain original behavior if not found
            print("Could not detect header row dynamically. Trying header=0.")
            df = pd.read_csv(filepath, header=0)
        else:
            # Reload with the correct header
            df = pd.read_csv(filepath, header=header_row_idx)

        # Clean column names
        df.columns = df.columns.astype(str).str.strip()
        
        # Rename map
        rename_map = {}
        for col in df.columns:
            c = col.lower()
            if 'section' in c: rename_map[col] = 'Section'
            elif 'weight' in c: rename_map[col] = 'Weight'
            elif 'ix' in c: rename_map[col] = 'Ix'
            elif 'zx' in c: rename_map[col] = 'Zx'
            elif 'area' in c: rename_map[col] = 'Area'
            elif c == 'h': rename_map[col] = 'h'
            elif c == 't': rename_map[col] = 't'
            
        df = df.rename(columns=rename_map)
        
        # Force 'Section' if not found but column 0 exists (Last Resort)
        if 'Section' not in df.columns and len(df.columns) > 0:
            rename_map[df.columns[0]] = 'Section'
            df = df.rename(columns=rename_map)
        
        # Ensure numeric columns are numeric
        numeric_cols = ['Weight', 'Ix', 'Zx', 'Area', 'h', 't']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with NaN in critical columns
        required = ['Section', 'Weight', 'Ix', 'Zx', 'Area', 'h', 't']
        # Filter only required cols that actually exist in df for dropna to avoid error
        existing_required = [c for c in required if c in df.columns]
        
        if existing_required:
            df = df.dropna(subset=existing_required)
        
        return df
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()

class SteelMaterial:
    """
    Class สำหรับจัดการคุณสมบัติทางกลของเหล็กโครงสร้างรูปพรรณขึ้นรูปเย็น
    
    อ้างอิงมาตรฐาน: มอก. 1228-2549 (TIS 1228-2549)
    เกรด: SSC400 (General Cold-formed steel)
    
    Attributes:
        Fy (float): กำลังจุดคราก (Yield Strength) ขั้นต่ำ
        Fu (float): กำลังต้านทานแรงดึง (Tensile Strength) ขั้นต่ำ
        E (float): โมดูลัสยืดหยุ่น (Modulus of Elasticity)
    """
    
    def __init__(self):
        # Base properties in MPa (N/mm^2) for Grade SSC400
        self.grade = "SSC400"
        self._fy_mpa = 245.0  # min
        self._fu_mpa = 400.0  # min
        self._e_mpa = 2.04e5  # Standard value
        
    def get_properties(self, thickness_mm, unit='MPa'):
        """
        คืนค่าคุณสมบัติทางกล (Mechanical Properties) ตามความหนา
        
        Args:
            thickness_mm (float): ความหนาของเหล็ก (mm)
            unit (str): หน่วยที่ต้องการ 'MPa' หรือ 'ksc' (default: 'MPa')
            
        Returns:
            dict: Dictionary ประกอบด้วย Fy, Fu, E, Elongation
        """
        # Determine Elongation based on TIS 1228-2549 Table 2
        if thickness_mm <= 5.0:
            elongation = 21.0 # %
        else:
            elongation = 17.0 # %
            
        # Unit Conversion Factor
        # 1 MPa = 10.19716 approx 10.197 ksc
        factor = 1.0
        if unit.lower() == 'ksc':
            factor = 10.197
            
        props = {
            'Grade': self.grade,
            'Fy': self._fy_mpa * factor,
            'Fu': self._fu_mpa * factor,
            'E': self._e_mpa * factor,
            'Elongation': elongation,
            'Unit': unit
        }
        
        return props

if __name__ == "__main__":
    # Example Usage
    steel = SteelMaterial()
    
    # Test 1: Thickness 3.2mm (<= 5mm), Unit MPa
    p1 = steel.get_properties(3.2, unit='MPa')
    print(f"Thickness 3.2mm (MPa): {p1}")
    
    # Test 2: Thickness 6.0mm (> 5mm), Unit ksc
    p2 = steel.get_properties(6.0, unit='ksc')
    print(f"Thickness 6.0mm (ksc): {p2}")

