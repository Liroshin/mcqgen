import os
import json
import traceback
import pandas as pd
import subprocess
from dotenv import load_dotenv
import streamlit as st
from src.mcqGenerator.utils import read_file
from src.mcqGenerator.logger import logging

# Load environment variables from .env file
load_dotenv()

# Load MCQ response template
with open(r'C:\Users\a882764\mcqgen\Response.json', 'r', encoding='utf-8') as file:
    RESPONSE_JSON = json.load(file)

# Streamlit App Title
st.title("MCQs Creator Application with ELiza")

# Streamlit Form for inputs
with st.form("user_inputs"):
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    mcq_count = st.number_input("No. of MCQs", min_value=3, max_value=50)
    subject = st.text_input("Insert Subject", max_chars=20)
    tone = st.text_input("Complexity Level of Questions", max_chars=20, placeholder="Simple")
    button = st.form_submit_button("Create MCQs")

    if button and uploaded_file is not None and mcq_count and subject and tone:
        with st.spinner("Generating MCQs..."):
            try:
                # Step 1: Read uploaded file content
                text = read_file(uploaded_file)

                # Step 2: Prepare quiz prompt with RESPONSE_JSON template included
                quiz_prompt = f"""
Text: {text}
You are an expert MCQ maker. Given the above text, it is your job to \
create a quiz of {mcq_count} multiple choice questions for {subject} students in a {tone} tone. 
Make sure the questions are not repeated and that all questions conform to the text.
Make sure to format your response like RESPONSE_JSON below and use it as a guide. \
Ensure to make exactly {mcq_count} MCQs.

### RESPONSE_JSON
{json.dumps(RESPONSE_JSON)}
"""

                # Step 3: Create API payload
                quiz_payload = {
                    "tool": "my-new-tool1",
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": quiz_prompt}],
                    "temperature": 0.2,
                    "stream": False,
                    "websearch": False
                }

                # Save payload to file
                with open("payload.json", "w", encoding="utf-8") as f:
                    json.dump(quiz_payload, f, indent=2)

                # Step 4: Execute cURL command to call API
                curl_command = [
                    "curl", "https://api.eliza-staging.myatos.net/api/assignmentfromsam/chat",
                    "-H", "Content-Type: application/json",
                    "-H", "api-key: sK1leK6JUj%ZRY!NMwMi",
                    "-H", "accept: */*",
                    "-d", "@payload.json"
                ]

                result = subprocess.run(curl_command, capture_output=True, text=True)

                if result.returncode != 0:
                    raise RuntimeError("❌ cURL command failed.")

                raw_response = result.stdout.strip()

                # Step 5: Parse the full response JSON
                response_dict = json.loads(raw_response)

               

                # Step 6: Extract and parse the quiz JSON string inside "answer"
                if "answer" in response_dict:
                    try:
                        quiz = json.loads(response_dict["answer"])  # parse inner JSON string
                    except json.JSONDecodeError:
                        st.error("⚠️ Failed to decode the quiz JSON inside the 'answer' field.")
                        st.text_area("Raw Answer Content", value=response_dict["answer"])
                        quiz = None
                else:
                    st.error("⚠️ 'answer' field not found in the API response.")
                    quiz = None

                # Step 7: Convert quiz dict to table format and display
                if quiz and isinstance(quiz, dict):
                    quiz_table_data = []
                    for key, value in quiz.items():
                        if isinstance(value, dict) and "mcq" in value:
                            mcq = value.get("mcq", "")
                            options = value.get("options", {})
                            option_str = " | ".join([f"{k}: {v}" for k, v in options.items()])
                            correct = value.get("correct", "")
                            quiz_table_data.append({
                                "Question": mcq,
                                "Options": option_str,
                                "Correct Answer": correct
                            })
                        else:
                            st.warning(f"⚠️ Unexpected quiz format in item: {key}")

                    if quiz_table_data:
                        df = pd.DataFrame(quiz_table_data)
                        df.index += 1
                        st.subheader("Generated MCQs")
                        st.dataframe(df)
                    else:
                        st.warning("⚠️ No valid MCQs were parsed.")
                else:
                    st.error("❌ Quiz data not found or invalid.")

            except Exception as e:
                st.error("❌ An error occurred while generating MCQs.")
                traceback.print_exception(type(e), e, e.__traceback__)
