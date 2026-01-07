import pdfplumber

pdf_path = "มอก. 1228-2549 เหล็กโครงสร้างรูปพรรณขึ้นรูปเย็น.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total Pages: {len(pdf.pages)}")
        
        # Scan pages
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"--- Page {i+1} ---")
            if text:
                print(text[:200].replace('\n', ' '))
            else:
                print("(No text extracted)")
            
            tables = page.extract_tables()
            if tables:
                print(f"Tables found: {len(tables)}")
                    
except Exception as e:
    print(f"Error: {e}")
