from groq import Groq
from dotenv import load_dotenv
import os
import PyPDF2

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Step 1: Read the PDF
def extract_text_from_pdf(filename):
    text = ""
    with open(filename, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        
        # Only read first 5 pages to stay within free tier limits
        pages_to_read = min(5, len(reader.pages))
        
        for i in range(pages_to_read):
            text += reader.pages[i].extract_text()
    
    # Extra safety: cut off at 3000 words
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000])
    
    return text

# Step 2: Send text to AI and get test cases back
def generate_test_cases(document_text):
    prompt = f"""
    You are a software testing expert. 
    Based on the following requirements document, generate 5 test cases.
    
    For each test case, provide:
    - Test Case ID (e.g. TC001)
    - Requirement (which requirement it tests e.g. FR26)
    - Description (what is being tested)
    - Pre-condition (what needs to be true before the test)
    - Test Steps (numbered steps to execute the test)
    - Expected Result (what should happen if it passes)
    - Priority (High, Medium, or Low)
    
    Format each test case clearly with these exact labels.
    
    Requirements document:
    {document_text}
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

# Run it
document_text = extract_text_from_pdf("sample.pdf")
print("PDF read successfully. Sending to AI...")
print("---")

test_cases = generate_test_cases(document_text)
print(test_cases)