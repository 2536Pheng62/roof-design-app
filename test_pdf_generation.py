"""Test script to debug PDF generation issues"""
from data_utils import load_data, DEFAULT_FILENAME, SteelMaterial
from purlin_design import PurlinDesign
from report_generator import ReportGenerator

# Load section data
df = load_data(DEFAULT_FILENAME)
if df.empty:
    print("ERROR: Failed to load section data")
    exit(1)

# Select first section
section_data = df.iloc[0].to_dict()
print(f"Selected section: {section_data.get('Section')}")

# Setup inputs
inputs = {
    'geometry': {'spacing': 1.0, 'span': 4.0, 'slope': 5.0},
    'loads': {'DL': 10.0, 'LL': 30.0, 'WL': 50.0},
    'materials': {'Fy': 2400.0, 'E': 2000000.0}
}

# Run design calculation
designer = PurlinDesign(section_data, inputs['geometry'], inputs['loads'], inputs['materials'])
results = designer.run_design()
print(f"Design calculation completed. Steps: {len(results.get('Steps', []))}")

# Generate PDF
proj_info = {
    "Project Name": "Test Project",
    "Owner": "Test Owner", 
    "Engineer": "Test Engineer"
}

print("\nGenerating PDF...")
try:
    gen = ReportGenerator(proj_info, inputs, results, section_data)
    success, result_path = gen.generate("test_output.pdf")
    
    if success:
        print(f"✅ PDF generated successfully: {result_path}")
        import os
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"File size: {file_size} bytes")
        else:
            print(f"⚠️ WARNING: Success reported but file doesn't exist at {result_path}")
    else:
        print(f"❌ PDF generation failed: {result_path}")
        
except Exception as e:
    print(f"❌ Exception during PDF generation: {e}")
    import traceback
    traceback.print_exc()
