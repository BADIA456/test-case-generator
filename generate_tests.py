from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import PyPDF2
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# This is Pydantic - we're defining exactly what one test case looks like
class TestCase(BaseModel):
    id: str
    requirement: str
    description: str
    precondition: str
    steps: str
    expected_result: str
    priority: str

class TestCaseList(BaseModel):
    test_cases: list[TestCase]

# Read PDF
def extract_text_from_pdf(filename):
    text = ""
    with open(filename, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        
        pages_to_read = min(5, len(reader.pages))
        for i in range(pages_to_read):
            text += reader.pages[i].extract_text()
    
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000])
    
    return text

# Send to AI and get structured JSON back
def generate_test_cases(document_text):
    prompt = f"""
    You are a software testing expert.
    Based on the following requirements document, generate 5 test cases.
    
    You must respond with ONLY a JSON object, no other text.
    The JSON must follow this exact structure:
    {{
        "test_cases": [
            {{
                "id": "TC001",
                "requirement": "FR1",
                "description": "what is being tested",
                "precondition": "what must be true before the test",
                "steps": "1. First step 2. Second step 3. Third step",
                "expected_result": "what should happen if test passes",
                "priority": "High"
            }}
        ]
    }}
    
    Priority must be exactly one of: High, Medium, Low
    Generate exactly 5 test cases.
    Respond with JSON only, no markdown, no explanation.
    
    Requirements document:
    {document_text}
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    raw = response.choices[0].message.content

    # Sometimes AI returns markdown code blocks like ```json ... ```
    # This strips that out if present
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    # Print raw so we can see what the AI actually returned
    print("AI returned:")
    print(raw)
    print("---")

    # Parse the JSON the AI returned
    data = json.loads(raw)
    
    # Validate it with Pydantic
    result = TestCaseList(**data)
    
    return result

# Run it
document_text = extract_text_from_pdf("sample.pdf")
print("PDF read successfully. Sending to AI...")
print("---")

result = generate_test_cases(document_text)

# Print each test case cleanly
for tc in result.test_cases:
    print(f"ID: {tc.id}")
    print(f"Requirement: {tc.requirement}")
    print(f"Description: {tc.description}")
    print(f"Precondition: {tc.precondition}")
    print(f"Steps: {tc.steps}")
    print(f"Expected Result: {tc.expected_result}")
    print(f"Priority: {tc.priority}")
    print("---")