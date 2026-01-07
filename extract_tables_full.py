import pdfplumber

pdf_path = "มอก. 1228-2549 เหล็กโครงสร้างรูปพรรณขึ้นรูปเย็น.pdf"

with open("tables_dump.txt", "w", encoding="utf-8") as f:
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                f.write(f"\n--- Page {i+1} Found {len(tables)} tables ---\n")
                for j, table in enumerate(tables):
                    f.write(f"Table {j+1}:\n")
                    for row in table:
                        # Clean row for readability
                        clean_row = [str(cell).replace('\n', ' ') if cell else "" for cell in row]
                        f.write(str(clean_row) + "\n")
