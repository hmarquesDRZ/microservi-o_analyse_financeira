# Financial Report Analyst

A Streamlit web app that uses OpenAI's assistants API to analyze financial statements. Upload PDF financial statements and chat with an AI analyst to get detailed insights.

## Features

- Upload multiple PDF financial statements
- Chat with an AI assistant to analyze the financial data
- Get comprehensive financial reports and analyses
- Visualize key financial metrics and trends

## Setup Instructions

### 1. Installation

```bash
# Clone the repository (or download the files)
git clone <repository-url>
cd <repository-directory>

# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

### 2. API Key Setup

You have three options for setting up your OpenAI API key:

1. **Enter it in the app**: You can paste your API key directly in the app when prompted.

2. **Environment variable**: Set the API key as an environment variable before running the app.
   ```bash
   # On Windows:
   set OPENAI_API_KEY=sk-your-api-key
   # On macOS/Linux:
   export OPENAI_API_KEY=sk-your-api-key
   ```

3. **Streamlit secrets**: Create a `.streamlit/secrets.toml` file with your API key:
   ```toml
   OPENAI_API_KEY = "sk-your-api-key"
   ```

### 3. Run the App

```bash
streamlit run app.py
```

## Usage

1. Enter your OpenAI API key if prompted
2. Upload your PDF financial statements using the sidebar uploader
3. Ask questions about the financial data in the chat input field
4. View the AI's analysis in the chat interface

## Example Queries

- "Give me a comprehensive analysis of the company's financial health."
- "What are the key profitability ratios and what do they indicate?"
- "Compare the liquidity position over the last two years."
- "What are the main risk factors based on these financial statements?"
- "Analyze the cash flow trends and their implications."

## Notes

- Files are uploaded to OpenAI and processed with the File Search tool
- File Search allows the AI to search and extract information from your PDFs
- Each file has a maximum size limit of 512 MB 