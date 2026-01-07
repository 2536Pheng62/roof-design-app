from report_generator import ReportGenerator
from purlin_design import PurlinDesign
import os

def test_report():
    print("Testing Report Generator...")
    
    # Mock Data
    proj = {
        'Project Name': 'Test Project',
        'Owner': 'Test Owner',
        'Engineer': 'Test Eng'
    }
    
    inputs = {
        'geometry': {'spacing': 1.0, 'span': 4.0, 'slope': 5.0},
        'loads': {'DL': 10, 'LL': 30, 'WL': 50},
        'materials': {'Fy': 2400, 'E': 2000000}
    }
    
    sec = {
        'Section': 'C-100x50x20x3.2',
        'Weight': 5.5,
        'Ix': 78.6,
        'Zx': 15.7,
        'h': 100,
        't': 3.2
    }
    
    # Replace hardcoded results with design calculation
    # 3. Design Calculation (To get full structure including Steps)
    designer = PurlinDesign(sec, inputs['geometry'], inputs['loads'], inputs['materials'])
    results = designer.run_design()
    
    # Generate
    gen = ReportGenerator(proj, inputs, results, sec)
    success, path = gen.generate("test_report.pdf")
    
    if success:
        print(f"PASS: Report generated at {path}")
        if os.path.exists(path):
            print(f"File size: {os.path.getsize(path)} bytes")
    else:
        print(f"FAIL: {path}")

if __name__ == "__main__":
    test_report()
