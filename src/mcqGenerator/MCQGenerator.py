import sys
import os
import json
import traceback
import pandas as pd
import subprocess
from dotenv import load_dotenv
from src.mcqGenerator.utils import read_file, get_table_data
from src.mcqGenerator.logger import logging

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

# Load env variables
load_dotenv()

# Input file
file_path = os.path.join(project_root, "data.txt")
TEXT = read_file(file_path)

# Sample MCQ response structure for formatting
RESPONSE_JSON = {
    "1": {"mcq": "multiple choice question", "options": {"a": "choice", "b": "choice", "c": "choice", "d": "choice"}, "correct": "correct answer"},
    "2": {"mcq": "multiple choice question", "options": {"a": "choice", "b": "choice", "c": "choice", "d": "choice"}, "correct": "correct answer"},
    "3": {"mcq": "multiple choice question", "options": {"a": "choice", "b": "choice", "c": "choice", "d": "choice"}, "correct": "correct answer"}
}

NUMBER = 5
SUBJECT = "biology"
TONE = "simple"

# Step 1: Quiz Generation Prompt
quiz_prompt = f"""
Text: {TEXT}
You are an expert MCQ maker. Given the above text, it is your job to \
create a quiz of {NUMBER} multiple choice questions for {SUBJECT} students in a {TONE} tone. 
Make sure the questions are not repeated and that all questions conform to the text.
Make sure to format your response like RESPONSE_JSON below and use it as a guide. \
Ensure to make exactly {NUMBER} MCQs.

### RESPONSE_JSON
{json.dumps(RESPONSE_JSON)}
"""

# Build JSON payload for quiz generation
quiz_payload = {
    "tool": "my-new-tool1",
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": quiz_prompt}],
    "temperature": 0.2,
    "stream": False,
    "websearch": False
}

with open("payload.json", "w", encoding="utf-8") as f:
    json.dump(quiz_payload, f, indent=2)

# Step 2: Call API using subprocess curl
try:
    curl_command = [
        "curl", "https://api.eliza-staging.myatos.net/api/assignmentfromsam/chat",
        "-H", "Content-Type: application/json",
        "-H", "api-key: sK1leK6JUj%ZRY!NMwMi",
        "-H", "accept: */*",
        "-d", "@payload.json"
    ]

    result = subprocess.run(curl_command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError("cURL command failed")

    raw_response = result.stdout.strip()
    print("✅ Raw Quiz Output:\n", raw_response)

    try:
        quiz_json = json.loads(raw_response)
    except json.JSONDecodeError:
        raise ValueError("Response is not valid JSON")

    # Step 3: Evaluation Prompt (manual second chain)
    quiz_str = json.dumps(quiz_json, indent=2)

    evaluation_prompt = f"""
You are an expert English grammarian and writer. Given a Multiple Choice Quiz for {SUBJECT} students,
evaluate the complexity of the questions and provide a brief (max 50 words) complexity analysis. 
If the quiz is not appropriate for the students' cognitive level, update the necessary questions and adjust the tone.

Quiz_MCQs:
{quiz_str}

Check from an expert English Writer of the above quiz:
"""

    eval_payload = {
        "tool": "my-new-tool1",
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": evaluation_prompt}],
        "temperature": 0.2,
        "stream": False,
        "websearch": False
    }

    with open("eval_payload.json", "w", encoding="utf-8") as f:
        json.dump(eval_payload, f, indent=2)

    eval_command = [
        "curl", "https://api.eliza-staging.myatos.net/api/assignmentfromsam/chat",
        "-H", "Content-Type: application/json",
        "-H", "api-key: sK1leK6JUj%ZRY!NMwMi",
        "-H", "accept: */*",
        "-d", "@eval_payload.json"
    ]

    eval_result = subprocess.run(eval_command, capture_output=True, text=True)

    if eval_result.returncode != 0:
        raise RuntimeError("Evaluation cURL command failed")

    eval_text = eval_result.stdout.strip()
    print("\n✅ Evaluation Output:\n", eval_text)

    # Step 4: Convert Quiz to Table
    quiz_table_data = []
    for key, value in quiz_json.items():
        mcq = value.get("mcq", "")
        options = " | ".join(f"{opt}: {opt_text}" for opt, opt_text in value.get("options", {}).items())
        correct = value.get("correct", "")
        quiz_table_data.append({"MCQ": mcq, "Choices": options, "Correct": correct})

    quiz_df = pd.DataFrame(quiz_table_data)
    display(quiz_df)

except Exception as e:
    print("❌ An error occurred:")
    traceback.print_exc()
