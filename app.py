import streamlit as st
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import PyPDF2
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Pydantic models
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

# PDF reader (my eyes are burning nowwwww)
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

# AI generator 
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

# getting the priority for testcases with colours
def get_priority_color(priority):
    if priority == "High":
        return ":red[HIGH]"
    elif priority == "Medium":
        return ":orange[MEDIUM]"
    else:
        return ":green[LOW]"

#  Streamlit UI -everything looks pretty now
st.set_page_config(page_title="Test Case Generator", layout="wide")

st.title("AI Test Case Generator")
st.write("Upload a requirements document and let AI generate test cases for you.")

# File uploader 
uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("Generate Test Cases"):
        with st.spinner("Reading document and generating test cases..."):
            document_text = extract_text_from_pdf(uploaded_file)
            result = generate_test_cases(document_text)
            
            # Save test cases to session state
            # Each test case also gets a "status" — starts as Todo
            st.session_state.test_cases = [
                {
                    "id": tc.id,
                    "requirement": tc.requirement,
                    "description": tc.description,
                    "precondition": tc.precondition,
                    "steps": tc.steps,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority,
                    "status": "Todo"  # this thing tracks which column the card is in
                }
                for tc in result.test_cases
            ]

# Kanban Board
if "test_cases" in st.session_state:
    st.divider()
    st.subheader("Test Case Kanban Board")
    
    # Creating 3 columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("###  To Do")
        st.caption("Test cases not yet executed")
        
        for i, tc in enumerate(st.session_state.test_cases):
            if tc["status"] == "Todo":
                with st.container(border=True):
                    st.markdown(f"**{tc['id']}** {get_priority_color(tc['priority'])}")
                    st.write(tc["description"])
                    
                    with st.expander("View details"):
                        st.write(f"**Requirement:** {tc['requirement']}")
                        st.write(f"**Precondition:** {tc['precondition']}")
                        st.write(f"**Steps:** {tc['steps']}")
                        st.write(f"**Expected Result:** {tc['expected_result']}")
                        st.write(f"**Priority:** {tc['priority']}")
                    
                    # Two buttons side by side
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Pass", key=f"pass_{i}"):
                            st.session_state.test_cases[i]["status"] = "Passed"
                            st.rerun()
                    with b2:
                        if st.button("Fail", key=f"fail_{i}"):
                            st.session_state.test_cases[i]["status"] = "Failed"
                            st.rerun()

    with col2:
        st.markdown("###  Passed")
        st.caption("Test cases that passed")
        
        for i, tc in enumerate(st.session_state.test_cases):
            if tc["status"] == "Passed":
                with st.container(border=True):
                    st.markdown(f"**{tc['id']}** {get_priority_color(tc['priority'])}")
                    st.write(tc["description"])
                    
                    with st.expander("View details"):
                        st.write(f"**Requirement:** {tc['requirement']}")
                        st.write(f"**Precondition:** {tc['precondition']}")
                        st.write(f"**Steps:** {tc['steps']}")
                        st.write(f"**Expected Result:** {tc['expected_result']}")
                        st.write(f"**Priority:** {tc['priority']}")
                    
                    # Allow moving back to Todo or to Failed
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Reset", key=f"reset_{i}"):
                            st.session_state.test_cases[i]["status"] = "Todo"
                            st.rerun()
                    with b2:
                        if st.button("Fail", key=f"fail2_{i}"):
                            st.session_state.test_cases[i]["status"] = "Failed"
                            st.rerun()

    with col3:
        st.markdown("###  Failed")
        st.caption("Test cases that failed")
        
        for i, tc in enumerate(st.session_state.test_cases):
            if tc["status"] == "Failed":
                with st.container(border=True):
                    st.markdown(f"**{tc['id']}** {get_priority_color(tc['priority'])}")
                    st.write(tc["description"])
                    
                    with st.expander("View details"):
                        st.write(f"**Requirement:** {tc['requirement']}")
                        st.write(f"**Precondition:** {tc['precondition']}")
                        st.write(f"**Steps:** {tc['steps']}")
                        st.write(f"**Expected Result:** {tc['expected_result']}")
                        st.write(f"**Priority:** {tc['priority']}")
                    
                    # Allow moving back to Todo or to Passed
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Reset", key=f"reset2_{i}"):
                            st.session_state.test_cases[i]["status"] = "Todo"
                            st.rerun()
                    with b2:
                        if st.button("Pass", key=f"pass2_{i}"):
                            st.session_state.test_cases[i]["status"] = "Passed"
                            st.rerun()