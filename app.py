import os
import google.generativeai as genai
from flask import Flask, request, jsonify
import json
import PyPDF2
import io
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)

ANALYZED_DOCUMENTS = []
DOCUMENT_ID_COUNTER = 0


try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set. For local testing, ensure it's in a .env file.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except (AttributeError, ValueError) as e:
    print(f"FATAL ERROR: Could not configure AI. Details: {e}")
    exit()

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

SUMMARY_PROMPT = 'Provide a concise, easy-to-understand, and user-friendly summary of the following legal text. The summary must be in **{language}**.\n\nText: "{text}"'
OBLIGATIONS_PROMPT = 'List the key responsibilities the primary user MUST take, based on the text. Make the points short and easy to read. The list items must be in **{language}**.\n\nText: "{text}"'
RIGHTS_PROMPT = 'List the key entitlements and permissions the primary user HAS, based on the text. Make the points short and easy to read. The list items must be in **{language}**.\n\nText: "{text}"'
RISKS_PROMPT = 'As a risk analyst for **{jurisdiction}**, identify potential red flags. Make the points concise and user-friendly. The list items must be in **{language}**.\n\nText: "{text}"'
QUESTIONS_PROMPT = 'Based on the identified risks, generate a list of simple, polite questions the user should ask for clarification. The questions must be in **{language}**.\n\nIdentified Risks: "{risks}"'

def clean_and_parse_json_list(response_text, key):
    clean_text = response_text.strip().replace('```json', '').replace('```', '')
    try:
        data = json.loads(clean_text)
        value = data.get(key, [])
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        return [line.strip() for line in clean_text.split('\n') if line.strip() and not line.strip().startswith('```')]

def analyze_text_logic(text, jurisdiction, language):
    summary_response = model.generate_content(SUMMARY_PROMPT.format(text=text, language=language), safety_settings=SAFETY_SETTINGS)
    obligations_response = model.generate_content(f'Respond in JSON format with a key "obligations". {OBLIGATIONS_PROMPT.format(text=text, language=language)}', safety_settings=SAFETY_SETTINGS)
    rights_response = model.generate_content(f'Respond in JSON format with a key "rights". {RIGHTS_PROMPT.format(text=text, language=language)}', safety_settings=SAFETY_SETTINGS)
    risks_response = model.generate_content(f'Respond in JSON format with a key "risks". {RISKS_PROMPT.format(text=text, jurisdiction=jurisdiction, language=language)}', safety_settings=SAFETY_SETTINGS)

    summary = summary_response.text.strip().replace('**', '')
    obligations = clean_and_parse_json_list(obligations_response.text, "obligations")
    rights = clean_and_parse_json_list(rights_response.text, "rights")
    risks = clean_and_parse_json_list(risks_response.text, "risks")

    questions_response = model.generate_content(f'Respond in JSON format with a key "questions". {QUESTIONS_PROMPT.format(risks=", ".join(risks), language=language)}', safety_settings=SAFETY_SETTINGS)
    questions = clean_and_parse_json_list(questions_response.text, "questions")

    return {
        "summary": summary,
        "obligations": obligations,
        "rights": rights,
        "risks": risks,
        "questions": questions
    }

@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/clarify-text', methods=['POST'])
def clarify_pasted_text():
    try:
        data = request.get_json()
        text = data.get('text')
        jurisdiction = data.get('jurisdiction', 'General / Non-Specific')
        language = data.get('language', 'English')
        
        if not text:
            return jsonify({"error": "No text provided."}), 400
            
        result = analyze_text_logic(text, jurisdiction, language)
        
        global DOCUMENT_ID_COUNTER
        DOCUMENT_ID_COUNTER += 1
        document_entry = {
            "id": DOCUMENT_ID_COUNTER,
            "type": "Pasted Text",
            "name": f"{text[:40]}...",
            "summary": result['summary']
        }
        ANALYZED_DOCUMENTS.append(document_entry)
        
        return jsonify(result)

    except Exception as e:
        print(f"Error in /clarify-text: {e}")
        return jsonify({"error": "Failed to process the text."}), 500

@app.route('/upload-and-clarify', methods=['POST'])
def upload_and_clarify_document():
    try:
        if 'document' not in request.files:
            return jsonify({"error": "No document part in the request."}), 400
        
        file = request.files['document']
        jurisdiction = request.form.get('jurisdiction', 'General / Non-Specific')
        language = request.form.get('language', 'English')

        if file.filename == '':
            return jsonify({"error": "No selected file."}), 400

        full_text = ""
        if file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in pdf_reader.pages:
                full_text += page.extract_text() or ""
        elif file.filename.endswith('.txt'):
            full_text = file.read().decode('utf-8')
        else:
            return jsonify({"error": "Unsupported file type. Please upload a PDF or .txt file."}), 400
        
        if not full_text.strip():
            return jsonify({"error": "Could not extract text from the document."}), 400

        result = analyze_text_logic(full_text, jurisdiction, language)
        
        global DOCUMENT_ID_COUNTER
        DOCUMENT_ID_COUNTER += 1
        document_entry = {
            "id": DOCUMENT_ID_COUNTER,
            "type": f"{file.filename.split('.')[-1].upper()} Document",
            "name": file.filename,
            "summary": result['summary']
        }
        ANALYZED_DOCUMENTS.append(document_entry)

        return jsonify(result)

    except Exception as e:
        print(f"Error in /upload-and-clarify: {e}")
        return jsonify({"error": "Failed to process the document."}), 500

@app.route('/list-documents', methods=['GET'])
def list_documents():
    return jsonify(sorted(ANALYZED_DOCUMENTS, key=lambda x: x['id'], reverse=True))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

