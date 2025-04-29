import os
import time
from typing import List, Dict, Any

import streamlit as st
from openai import OpenAI

# -----------------------------
# Configuration
# -----------------------------

# Streamlit page config
st.set_page_config(
    page_title="Financial Report Analyst",
    page_icon="📊",
    layout="wide",
)

# ASSISTANT CONFIGURATION
ASSISTANT_NAME = "Financial Analyst Assistant"
ASSISTANT_INSTRUCTIONS = (
    "You are a seasoned financial analyst. Your job is to analyse any provided financial statements "
    "(balance sheets, income statements, cash-flow statements, etc.) and produce clear, comprehensive "
    "reports. Your reports should cover profitability, liquidity, solvency, efficiency ratios, trend analysis, "
    "and notable risks. Cite figures directly from the statements when relevant and explain their meaning."
)
ASSISTANT_MODEL = "gpt-4o"

# API Key handling - allow user input if not found in environment
api_key = os.getenv("OPENAI_API_KEY", "")

# If not in sidebar state or environment, show the input widget
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = api_key

if not st.session_state.openai_api_key:
    with st.sidebar:
        st.session_state.openai_api_key = st.text_input(
            "Enter your OpenAI API key",
            type="password",
            help="Get your API key from https://platform.openai.com/account/api-keys",
            placeholder="sk-..."
        )
        st.markdown("""
        💡 **Tip:** To avoid entering your API key each time:
        1. Set it as an environment variable: `OPENAI_API_KEY=sk-...`
        2. Or create a `.streamlit/secrets.toml` file with:
           ```
           OPENAI_API_KEY = "sk-..."
           ```
        """)
        
if not st.session_state.openai_api_key:
    st.warning("Please enter your OpenAI API key to continue")
    st.stop()

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=st.session_state.openai_api_key)

# Session-level cache for assistant creation
@st.cache_resource(show_spinner=False)
def get_or_create_assistant(api_key) -> str:
    """Return an assistant_id, creating the assistant once per session if needed."""
    # Check if assistant_id is stored in session state first
    if "assistant_id" in st.session_state:
        return st.session_state.assistant_id
    
    # Check environment variable as a fallback
    assistant_id = os.getenv("ASSISTANT_ID")
    if assistant_id:
        st.session_state.assistant_id = assistant_id
        return assistant_id
    
    # Initialize the client with the provided API key for assistant creation
    temp_client = OpenAI(api_key=api_key)
    
    with st.spinner("Creating analyst assistant… this is a one-time operation"):
        try:
            assistant = temp_client.beta.assistants.create(
                name=ASSISTANT_NAME,
                instructions=ASSISTANT_INSTRUCTIONS,
                model=ASSISTANT_MODEL,
                tools=[{"type": "file_search"}],
            )
            st.session_state.assistant_id = assistant.id
            # Optionally persist this in an env var or database if needed long-term
            return assistant.id
        except Exception as e:
            st.error(f"Failed to create assistant: {e}")
            st.stop()

assistant_id = get_or_create_assistant(st.session_state.openai_api_key)

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📊 Financial Report Analyst")
st.caption(
    "Upload one or more PDF financial statements and chat to get detailed analyses and reports."
)

# Initial session states
if "file_ids" not in st.session_state:
    st.session_state.file_ids: List[str] = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id: str | None = None
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, Any]] = []  # list of dict(role, content)
if "uploaded" not in st.session_state:
    st.session_state.uploaded: List[Dict[str, str]] = []

# Sidebar uploader
st.sidebar.header("Upload PDF Financial Statements")
uploaded_files = st.sidebar.file_uploader(
    "Choose one or more PDF files", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    newly_uploaded_ids = []
    for uploaded_file in uploaded_files:
        if uploaded_file is None:
            continue
        # Check against names already in the session state list
        if uploaded_file.name in [meta["name"] for meta in st.session_state.uploaded]:
            continue  # Skip duplicates in same run

        try:
            with st.spinner(f"Uploading {uploaded_file.name} …"):
                api_file = client.files.create(
                    file=(uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type),
                    purpose="assistants",
                )
            st.session_state.file_ids.append(api_file.id)
            st.session_state.uploaded.append({"name": uploaded_file.name, "id": api_file.id})
            newly_uploaded_ids.append(api_file.id)
            st.sidebar.success(f"Uploaded {uploaded_file.name}")
        except Exception as e:
            st.sidebar.error(f"Failed to upload {uploaded_file.name}: {e}")
    # Clear the list of file IDs to re-add all current ones in the next message
    # This ensures all currently uploaded files are attached to the next message
    # st.session_state.file_ids = [meta["id"] for meta in st.session_state.uploaded]

# Display uploaded files list
st.sidebar.subheader("Attached files")
if st.session_state.uploaded:
    for meta in st.session_state.uploaded:
        st.sidebar.write(f"• {meta['name']} (id: {meta['id']})")
else:
    st.sidebar.write("No files uploaded yet.")

# Chat interface
st.divider()
chat_container = st.container()
user_input = st.chat_input("Ask something about the financial statements…")

# Render chat history
with chat_container:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

# Handle new user message
if user_input:
    # Append user message to chat history for display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        st.chat_message("user").markdown(user_input)

    # Create thread if first interaction
    if st.session_state.thread_id is None:
        try:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            st.stop()
    else:
        # Fetch existing thread (optional, could assume it exists)
        try:
            thread = client.beta.threads.retrieve(st.session_state.thread_id)
        except Exception as e:
            st.error(f"Failed to retrieve thread: {e}")
            st.stop() # Or handle differently, maybe try creating a new one

    # Prepare attachments for the message
    current_file_ids = [meta["id"] for meta in st.session_state.uploaded]
    attachments = []
    if current_file_ids:
        attachments = [
            {"file_id": file_id, "tools": [{"type": "file_search"}]} 
            for file_id in current_file_ids
        ]

    # Add the user's message to the thread with attachments
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
            attachments=attachments if attachments else None, # Pass attachments here
        )
    except Exception as e:
        st.error(f"Failed to send message: {e}")
        st.stop()

    # Create the run without file_ids
    try:
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            # No file_ids here
        )
    except Exception as e:
        st.error(f"Failed to start analysis run: {e}")
        st.stop()

    # Poll until completed
    with st.spinner("Analysing…"):
        while True:
            try:
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status in ("completed", "failed", "cancelled", "expired"):
                    break
                time.sleep(1)
            except Exception as e:
                st.error(f"Error checking run status: {e}")
                time.sleep(5) # Wait longer before retrying on error
                # Optionally break after too many errors

    if run.status != "completed":
        st.error(f"Analysis run failed or was cancelled/expired. Status: {run.status}")
    else:
        # Fetch assistant response(s)
        try:
            messages_page = client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
            # Check if messages were returned
            if messages_page.data:
                assistant_message = messages_page.data[0]
                # Ensure the latest message is from the assistant
                if assistant_message.role == "assistant":
                    assistant_content = ""
                    for content_part in assistant_message.content:
                        if content_part.type == "text":
                            assistant_content += content_part.text.value
                        # Handle other content types if necessary (e.g., images)
                    
                    # Append assistant message to chat history for display
                    st.session_state.messages.append({"role": "assistant", "content": assistant_content})
                    with chat_container:
                        st.chat_message("assistant").markdown(assistant_content)
                else:
                    st.warning("No new response from the assistant.") # Latest msg might be user's
            else:
                 st.warning("No messages found in the thread after the run.")

        except Exception as e:
            st.error(f"Failed to fetch assistant response: {e}") 