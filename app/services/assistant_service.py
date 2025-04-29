import asyncio
import json
import time
from openai import AsyncOpenAI
from fastapi import UploadFile # Use FastAPI's UploadFile

# Assuming schemas.analysis is in the python path or same directory level
from schemas.analysis import AnalysisResponse

class FinancialAssistantService:
    """Handles interactions with the OpenAI Assistant for financial analysis."""
    
    def __init__(self, client: AsyncOpenAI, assistant_id: str):
        if not client:
            raise ValueError("OpenAI client must be provided.")
        if not assistant_id:
            raise ValueError("Assistant ID must be provided.")
        self.client = client
        self.assistant_id = assistant_id
        print(f"FinancialAssistantService initialized with Assistant ID: {self.assistant_id}")

    async def _poll_run_and_extract_response(self, thread_id: str, run_id: str) -> AnalysisResponse:
        """Polls the run status and extracts the function call arguments when ready."""
        print("Polling for run completion...")
        while True:
            run = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            print(f"Run status: {run.status}")

            if run.status == "requires_action":
                print("Run requires action: Function call detected.")
                if run.required_action.type == "submit_tool_outputs":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    # Assuming only one function call ("submit_financial_analysis") is expected
                    if tool_calls and tool_calls[0].type == "function" and tool_calls[0].function.name == "submit_financial_analysis":
                        function_call = tool_calls[0].function
                        arguments_str = function_call.arguments
                        print(f"Raw arguments: {arguments_str}")
                        try:
                            arguments_dict = json.loads(arguments_str)
                            # Validate and parse using Pydantic
                            analysis_response = AnalysisResponse.model_validate(arguments_dict)
                            print("Function arguments successfully parsed and validated.")
                            # We don't need to submit tool outputs in this specific workflow
                            # The function arguments *are* the final result.
                            return analysis_response
                        except json.JSONDecodeError as e:
                            print(f"Error decoding function arguments JSON: {e}")
                            # Consider submitting an error tool output?
                            # For now, raise an exception to signal failure.
                            raise ValueError(f"Failed to decode function arguments: {e}")
                        except Exception as e: # Catch Pydantic validation errors etc.
                            print(f"Error validating function arguments: {e}")
                            raise ValueError(f"Invalid function arguments received from Assistant: {e}")
                    else:
                        # Handle cases with unexpected tool calls or no function call
                        print(f"Warning: Expected function call 'submit_financial_analysis' not found in required_action. Tool calls: {tool_calls}")
                        # Optionally submit empty tool outputs to let the run potentially complete/fail
                        # await self.client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run_id, tool_outputs=[])
                        raise ValueError("Assistant did not call the expected function.")
                else:
                    print(f"Warning: Unhandled required action type: {run.required_action.type}")
                    raise ValueError(f"Unhandled required action type: {run.required_action.type}")

            elif run.status == "completed":
                # This path should ideally not be reached if function calling is mandatory and correctly prompted
                print("Error: Run completed, but expected a function call.")
                # You might want to retrieve messages here for debugging, but the primary path failed.
                raise ValueError("Run completed without calling the required function.")

            elif run.status in ["failed", "cancelled", "expired"]:
                print(f"Run ended with status: {run.status}. Error: {run.last_error}")
                error_message = f"Analysis failed with status {run.status}."
                if run.last_error:
                    error_message += f" Details: {run.last_error.message}"
                raise RuntimeError(error_message)
            
            elif run.status in ["queued", "in_progress"]:
                 await asyncio.sleep(1) # Use asyncio.sleep for async polling
            
            else:
                # Should not happen based on documented statuses
                raise RuntimeError(f"Run ended with unexpected status: {run.status}")

    async def analyze_csv(self, file: UploadFile) -> AnalysisResponse:
        """Orchestrates the analysis process: upload, thread, message, run, poll, parse, delete."""
        uploaded_file_id = None
        thread_id = None
        
        try:
            # 1. Upload the file provided by the user
            print(f"Uploading file: {file.filename}...")
            api_file = await self.client.files.create(
                file=(file.filename, await file.read(), file.content_type),
                purpose="assistants"
            )
            uploaded_file_id = api_file.id
            print(f"File uploaded successfully. File ID: {uploaded_file_id}")

            # 2. Create a new thread for this analysis
            print("Creating new thread...")
            thread = await self.client.beta.threads.create()
            thread_id = thread.id
            print(f"Thread created successfully. Thread ID: {thread_id}")

            # 3. Create the message with the file attachment
            print(f"Creating message in thread {thread_id} with attachment {uploaded_file_id}...")
            user_message_content = f"Analyze the financial data in the attached file: {file.filename}"
            message = await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message_content,
                attachments=[
                    {"file_id": uploaded_file_id, "tools": [{"type": "file_search"}]}
                ]
            )
            print(f"Message created successfully. Message ID: {message.id}")

            # 4. Create and run the assistant on the thread
            print(f"Creating run for Assistant {self.assistant_id} on thread {thread_id}...")
            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
            )
            print(f"Run created successfully. Run ID: {run.id}")

            # 5. Poll for completion and extract the response
            analysis_response = await self._poll_run_and_extract_response(thread_id, run.id)
            return analysis_response

        except Exception as e:
            # Log the error appropriately in a real application
            print(f"An error occurred during analysis: {e}")
            # Re-raise or handle specific exceptions as needed
            raise # Re-raise the caught exception
        
        finally:
            # 7. Clean up: Delete the uploaded file
            if uploaded_file_id:
                try:
                    print(f"Deleting uploaded file: {uploaded_file_id}...")
                    await self.client.files.delete(uploaded_file_id)
                    print("File deleted successfully.")
                except Exception as delete_err:
                    # Log deletion error but don't necessarily fail the whole operation
                    print(f"Warning: Failed to delete file {uploaded_file_id}: {delete_err}")
            # Optionally delete the thread - maybe useful for debugging initially
            # if thread_id:
            #     try:
            #         print(f"Deleting thread: {thread_id}...")
            #         await self.client.beta.threads.delete(thread_id)
            #         print("Thread deleted successfully.")
            #     except Exception as delete_err:
            #         print(f"Warning: Failed to delete thread {thread_id}: {delete_err}") 