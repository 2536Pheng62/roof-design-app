from purlin_design import PurlinDesign
from data_utils import load_data, DEFAULT_FILENAME
import pandas as pd

def verify():
    output_lines = []
    output_lines.append("--- Starting Verification ---")
    
    # 1. Load Data
    df = load_data(DEFAULT_FILENAME)
    if df.empty:
        output_lines.append("FAIL: Data load failed")
    else:
        output_lines.append(f"PASS: Data loaded. {len(df)} sections found.")
    
        # 2. Select a section
        section_name = 'C-100x50x20x3.2'
        if section_name not in df['Section'].values:
            output_lines.append(f"WARN: Default section {section_name} not found. Using first available.")
            section_name = df['Section'].iloc[0]
            
        section_data = df[df['Section'] == section_name].iloc[0].to_dict()
        output_lines.append(f"Selected Section: {section_name}")
        output_lines.append(f"Section Data: {section_data}")
        
        # 3. Define Inputs (Standard Test Case)
        inputs = {
            'geometry': {'spacing': 1.0, 'span': 4.0, 'slope': 5.0},
            'loads': {'DL': 10.0, 'LL': 30.0, 'WL': 50.0},
            'materials': {'Fy': 2400.0, 'E': 2000000.0}
        }
        
        # 4. Run Design
        full_design = PurlinDesign(section_data, inputs['geometry'], inputs['loads'], inputs['materials'])
        results = full_design.run_design()
        
        # 5. Print Results for manual check
        output_lines.append("\n--- Results ---")
        output_lines.append(f"Loads (kg/m): {results['Loads']}")
        output_lines.append(f"Combinations (kg/m): {results['Combinations']}")
        output_lines.append(f"Internal Forces: {results['Forces']}")
        output_lines.append(f"Checks: {results['Checks']['Status']}")
        output_lines.append(f"Ratios: {results['Checks']['Ratios']}")
        
        # 6. Basic Assertions (Sanity Checks)
        try:
            assert results['Loads']['DL_line'] > 0
            assert results['Combinations']['Wu_design'] > 0
            assert results['Forces']['Mu_kgm'] > 0
            # 4. Check Steps (New)
            assert 'Steps' in results, "Steps key missing from results"
            assert len(results['Steps']) > 0, "Steps list is empty"
            print(f"Detailed Steps Count: {len(results['Steps'])}")

            print("\nPASS: Basic logic assertions passed.")
        except AssertionError:
            output_lines.append("\nFAIL: Basic logic assertions failed.")

    # Write to file
    with open("verification_results.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(output_lines))
    print("Verification complete. Results written to verification_results.txt")

if __name__ == "__main__":
    verify()
