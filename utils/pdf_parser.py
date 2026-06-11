import pdfplumber
import re
import json
from groq import Groq
import os


def extract_text_from_pdf(pdf_file) -> str:
    """Extract raw text from uploaded PDF."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def parse_pyq_with_llm(text: str, groq_api_key: str) -> dict:
    """Use Groq LLM to extract structured Q&A + metadata from raw PDF text."""
    client = Groq(api_key=groq_api_key)

    prompt = f"""You are a structured data extractor for university exam papers.

From the following exam paper text, extract:
1. Subject name
2. Exam type (Midsem / Endsem / Quiz / Assignment)
3. Academic year (e.g. 2023-24)
4. A list of all questions with their metadata

Return ONLY valid JSON, no markdown, no explanation. Use this exact schema:
{{
  "subject": "string",
  "exam_type": "string",
  "year": "string",
  "questions": [
    {{
      "question_number": "string",
      "question_text": "string",
      "marks": number or null,
      "topic": "string",
      "difficulty": "Easy" | "Medium" | "Hard"
    }}
  ]
}}

For topic, infer from the question content (e.g. TCP, Normalization, CPU Scheduling, etc.)
For difficulty: short definitions = Easy, explain/describe = Medium, calculate/analyze/compare = Hard

Exam paper text:
{text[:6000]}
"""

    response = client.chat.completions.create(
      model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)
