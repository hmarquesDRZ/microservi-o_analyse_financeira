import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from openai import OpenAI, AsyncOpenAI # Use Async client for FastAPI

# Assuming schemas and services are structured as planned
from schemas.analysis import AnalysisResponse
from app.services.assistant_service import FinancialAssistantService

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---
API_TITLE = "Financial Analysis Service"
API_VERSION = "0.1.0"
API_DESCRIPTION = "Receives a municipal budget CSV and returns a structured financial analysis using OpenAI Assistants."
# -------------------------

# --- Initialize OpenAI Client and Service ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
if not ASSISTANT_ID:
    # You might allow creation here, but for a stable service, it's better to pre-create
    raise ValueError("ASSISTANT_ID environment variable not set. Run scripts/create_assistant.py first.")

# Use AsyncOpenAI for compatibility with FastAPI async endpoints
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Instantiate the service
assistant_service = FinancialAssistantService(client=client, assistant_id=ASSISTANT_ID)
# ------------------------------------------

# --- FastAPI Application ---
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION
)

@app.post("/analyze", 
            response_model=AnalysisResponse, 
            summary="Analyze Financial CSV",
            description="Upload a CSV or PDF file containing municipal financial data. The service will process it using an OpenAI Assistant and return a structured JSON analysis including text and chart data.",
            tags=["Analysis"])
async def analyze_financial_data(file: UploadFile = File(..., description="The municipal budget CSV or PDF file to analyze.")):
    """
    Endpoint to receive a CSV or PDF file and return a structured financial analysis.
    """
    # Allow both CSV and PDF
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.csv') or filename_lower.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV or PDF file.")
    
    print(f"Received file: {file.filename}, content type: {file.content_type}")
    
    try:
        # Call the assistant service to perform the analysis
        analysis_result = await assistant_service.analyze_csv(file)
        print("Analysis successful. Returning structured response.")
        return analysis_result
    except ValueError as ve:
        # Handle validation errors or specific operational errors from the service
        print(f"Value Error during analysis: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        # Handle runtime errors from the assistant run (failed, cancelled, etc.)
        print(f"Runtime Error during analysis: {re}")
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        # Catch-all for any other unexpected errors
        print(f"Unexpected Error during analysis: {e}")
        # Log the full traceback here in a real application
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/health", 
         summary="Health Check", 
         description="Simple health check endpoint.",
         tags=["Monitoring"])
async def health_check():
    """
    Returns a simple success message to indicate the service is running.
    """
    return {"status": "ok"}

# --- Running the App (for local development) ---
# Use Uvicorn to run the app: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    # Note: Running directly like this is mainly for simple testing.
    # Production deployments should use a proper ASGI server setup.
    uvicorn.run(app, host="0.0.0.0", port=8000) 