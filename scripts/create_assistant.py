import json
import os
import pathlib
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (especially OPENAI_API_KEY)
load_dotenv()

# Define paths relative to the script location
ROOT_DIR = pathlib.Path(__file__).parent.parent
ASSISTANT_CONFIG_DIR = ROOT_DIR / "assistant_config"
INSTRUCTIONS_PATH = ASSISTANT_CONFIG_DIR / "instructions.md"
FUNCTION_SCHEMA_PATH = ASSISTANT_CONFIG_DIR / "analysis_function.json"

# --- Configuration ---
ASSISTANT_NAME = "Analista Financeiro Municipal v1"
ASSISTANT_MODEL = "gpt-4.1" # Or your preferred model
FUNCTION_NAME = "submit_financial_analysis"
FUNCTION_DESCRIPTION = "Submits the structured financial analysis based on the provided CSV."
# -------------------

def create_assistant():
    """Creates the OpenAI Assistant with instructions and function tool."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment.")
        return

    client = OpenAI(api_key=api_key)

    # --- Load Configuration Files ---
    try:
        with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
            instructions = f.read()
    except FileNotFoundError:
        print(f"Error: Instructions file not found at {INSTRUCTIONS_PATH}")
        return
    except IOError as e:
        print(f"Error reading instructions file: {e}")
        return
        
    try:
        with open(FUNCTION_SCHEMA_PATH, "r", encoding="utf-8") as f:
            function_schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: Function schema file not found at {FUNCTION_SCHEMA_PATH}")
        print("Did you run `python scripts/gen_schema.py` first?")
        return
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing function schema file: {e}")
        return
    # -----------------------------------

    print(f"Creating assistant '{ASSISTANT_NAME}' with model '{ASSISTANT_MODEL}'...")

    try:
        assistant = client.beta.assistants.create(
            name=ASSISTANT_NAME,
            instructions=instructions,
            model=ASSISTANT_MODEL,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": FUNCTION_NAME,
                        "description": FUNCTION_DESCRIPTION,
                        "parameters": function_schema,
                    }
                },
                {"type": "file_search"} # Tool needed to access files attached to messages
            ]
        )
        print(f"Assistant created successfully!")
        print(f"Assistant ID: {assistant.id}")
        print("\nPlease store this ID securely, for example, in your .env file as ASSISTANT_ID")
        
        # Optionally, write to .env or a config file
        # Be careful with automated writes to .env files
        # Example (use with caution):
        # with open(ROOT_DIR / ".env", "a") as f:
        #     f.write(f"\nASSISTANT_ID={assistant.id}")
        # print("ASSISTANT_ID appended to .env file.")
        
    except Exception as e:
        print(f"Error creating assistant: {e}")

if __name__ == "__main__":
    create_assistant() 