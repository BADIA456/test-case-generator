import PyPDF2

# Open the PDF file
with open("sample.pdf", "rb") as f:
    reader = PyPDF2.PdfReader(f)
    
    print("Number of pages:", len(reader.pages))
    print("---")
    
    # Loop through every page and print its text
    for i, page in enumerate(reader.pages):
        print(f"Page {i+1}:")
        print(page.extract_text())
        print("---")