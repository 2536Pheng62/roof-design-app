import pdfplumber

pdf_path = "มอก. 1228-2549 เหล็กโครงสร้างรูปพรรณขึ้นรูปเย็น.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            print(f"--- Page {i+1} Found {len(tables)} tables ---")
            for j, table in enumerate(tables):
                # Clean newlines from headers for display
                if table and len(table) > 0:
                    header = [str(c).replace('\n', ' ')[:20] for c in table[0] if c]
                    print(f"Table {j+1}: {header}")
                    # Print first data row to verify
                    if len(table) > 1:
                         print(f"Row 1: {table[1]}")
