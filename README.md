LexiClarify - Your AI Legal Companion
LexiClarify is an intelligent legal companion designed to demystify complex legal documents. Built for the Google Cloud Gen AI Exchange Hackathon, this tool transforms dense legal jargon into simple, actionable advice using Google's Gemini AI.

Key Features
Dual-Mode Input: Upload full PDF/.txt documents or paste single clauses directly.

Multilingual Analysis: Get results in multiple languages, including English, Hindi, Spanish, and more.

Jurisdiction-Aware: Risk analysis is tailored to your selected location for higher accuracy.

Actionable Insights: Provides a clear summary, a breakdown of your rights and obligations, a risk radar, and AI-generated questions to ask before signing.

Text-to-Speech: Listen to the analysis for greater accessibility.

Session History: Review your past analyses in a clean interface.

Tech Stack
Frontend: HTML5, CSS3, JavaScript, Bootstrap 5

Backend: Python 3, Flask

AI Engine: Google Gemini 1.5 Flash Pro

Libraries: PyPDF2 (for PDF processing), Gunicorn (for production server)

How to Run Locally
Clone the Repository:

git clone [https://github.com/your-username/lexiclarify.git](https://github.com/your-username/lexiclarify.git)
cd lexiclarify

Install Dependencies:

pip install -r requirements.txt

Set Up Environment Variable:

Create a file named .env in the root directory.

Add your Google Gemini API key to this file:

GOOGLE_API_KEY="your_secret_api_key_here"

Run the Application:

python app.py

Open your browser and navigate to http://127.0.0.1:5000.