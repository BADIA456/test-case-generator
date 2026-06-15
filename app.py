import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import PyPDF2
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---- Pydantic models (same as before) ----
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

# ---- PDF reader (same as before) ----
def extract_text_from_pdf(filename):
    text = ""
    reader = PyPDF2.PdfReader(filename)
    pages_to_read = min(5, len(reader.pages))
    for i in range(pages_to_read):
        text += reader.pages[i].extract_text()
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000])
    return text

# ---- AI generator (same as before) ----
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

    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    raw = raw.strip()
    if not raw.startswith("{"):
        raw = "{" + raw + "}"

    data = json.loads(raw)
    result = TestCaseList(**data)
    return result

# ---- Streamlit UI starts here ----

# This sets the browser tab title and layout
st.set_page_config(page_title="Test Case Generator", layout="wide")

# Main title on the page
st.title("AI Test Case Generator")
st.write("Upload a requirements document and let AI generate test cases for you.")

# File uploader widget
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

# Generate button
if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("Generate Test Cases"):
        # Show a spinner while AI is thinking
        with st.spinner("Reading document and generating test cases..."):
            document_text = extract_text_from_pdf(uploaded_file)
            result = generate_test_cases(document_text)
            
            # Save results to session state so they persist on the page
            st.session_state.test_cases = result.test_cases

# Display results if they exist
if "test_cases" in st.session_state:
    st.subheader("Generated Test Cases")
    
    for tc in st.session_state.test_cases:
        # Each test case gets its own expandable box
        with st.expander(f"{tc.id} — {tc.description}"):
            st.write(f"**Requirement:** {tc.requirement}")
            st.write(f"**Precondition:** {tc.precondition}")
            st.write(f"**Steps:** {tc.steps}")
            st.write(f"**Expected Result:** {tc.expected_result}")
            st.write(f"**Priority:** {tc.priority}")