# This Python script defines the OpenAIClient class for interacting with the OpenAI API.
# It initializes the OpenAI client and sets up system prompt instructions for handling different types
# of questions and output formats. The class serves as a wrapper around the OpenAI API, providing a 
# structured way to initialize and manage AI prompts and responses within the application.

import openai
from openai import OpenAI
from project_logging import logging_module
from parameter_config import OPENAI_API_KEY

class OpenAIClient:
    def __init__(self):
        """
        Initializes the OpenAIClient with all system prompts.
        """
        self.client = OpenAI(api_key=OPENAI_API_KEY)  # Initialize OpenAI client

        # System content strings
        self.val_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The text \"Context:\" followed by the contents of the pdf file is enclosed in triple backticks. \
The text \"Output Format:\" explains how the Question must be answered. You are an AI that reads the Question enclosed 
in triple backticks and provides the answer in the mentioned Output Format."""

        self.ann_system_content = """Every prompt will begin with the text \"Question:\" followed by the question \
enclosed in triple backticks. The text \"Context:\" followed by the contents of the pdf file is enclosed in triple backticks. \
The \"Annotator Steps:\" mentions the steps that you should take for answering the question. The text \"Output Format:\" \
explains how the Question output must be formatted. You are an AI that reads the Question enclosed in triple backticks \
and follows the Annotator Steps and provides the answer in the mentioned Output Format."""

        self.output_format = "Provide a clear and conclusive answer to the Question being asked. Do not provide any \
reasoning or references for your answer."

        self.assistant_instruction = """You are an assistant that answers any questions relevant to the \
file that is uploaded in the thread. """
    
    def format_content(self, question: str, annotator_steps: str = None) -> str:
        if annotator_steps is None:
            return f"Question: ```{question}```\nOutput Format: {self.output_format}\n"
        else:
            return f"Question: ```{question}```\nAnnotator Steps: {annotator_steps}\nOutput Format: {self.output_format}\n"
        
    def validation_prompt(self, question: str, model: str, annotator_steps: str = None, imageurl: str = None) -> str:
        if annotator_steps:
            user_content = self.format_content(question, annotator_steps)
            system_content = self.ann_system_content
        else:
            user_content = self.format_content(question)
            system_content = self.val_system_content
        try:
            logging_module.log_success(f"System Content: {system_content}")
            logging_module.log_success(f"User Content: {user_content}")

            if imageurl:     
                response = self.client.chat.completions.create(
                    model=model.lower(),
                    messages=[
                        {"role": "system", "content": system_content},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_content},
                                {"type": "image_url", 
                                "image_url": {
                                    "url": imageurl,
                                    "detail": "low"
                                    }
                                },
                            ],
                        }
                    ]
                )
            else:
                response = self.client.chat.completions.create(
                    model=model.lower(),
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content}
                    ]
                )

            logging_module.log_success(f"Response: {response.choices[0].message.content}")

            return response.choices[0].message.content
        
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
        
    def file_validation_prompt(self, file_path: str, question: str, model: str) -> str:
        user_content = self.format_content(question)
        system_content = self.val_system_content
        try:

            logging_module.log_success(f"System Content: {system_content}")
            logging_module.log_success(f"User Content: {user_content}")

            file_assistant = self.client.beta.assistants.create(
                instructions=self.assistant_instruction + system_content,
                model=model.lower(),
                tools=[{"type": "file_search"}],
            )

            logging_module.log_success(f"Assistant created with ID: {file_assistant.id}")

            query_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants")

            logging_module.log_success(f"File stored with ID: {query_file.id}")

            empty_thread = self.client.beta.threads.create()

            logging_module.log_success(f"Thread created with ID: {query_file.id}")

            self.client.beta.threads.messages.create(
                empty_thread.id,
                role="user",
                content=user_content,
                attachments=[{"file_id": query_file.id, "tools": [{"type": "file_search"}]}]
            )

            logging_module.log_success(f"Message created in thread {empty_thread.id} with file {query_file.id}")

            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=empty_thread.id,
                assistant_id=file_assistant.id,
                max_prompt_tokens=30000
            )

            logging_module.log_success(f"Run executed with ID: {run.id}")

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=run.thread_id
                )

                logging_module.log_success(f"Response: {messages.data[0].content[0].text.value}")

                self.cleanup_resources(file_assistant.id, query_file.id, empty_thread.id)

                return messages.data[0].content[0].text.value
            else:
                logging_module.log_error(f"Run Status: {run.status}")
                logging_module.log_error(f"Run Status: {run.last_error}")
                return None
            
        except openai.BadRequestError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except openai.APIError as e:
            logging_module.log_error(f"Error: {e}")
            return f"Error-BDIA: {e}"
        except Exception as e:
            logging_module.log_error(f"An unexpected error occurred: {str(e)}")
            return f"Error-BDIA: {e}"
    
    def cleanup_resources(self, assistant_id: str, file_id: str, thread_id: str) -> None:
        try:
            # Delete the assistant
            self.client.beta.assistants.delete(assistant_id)
            logging_module.log_success(f"Assistant with {assistant_id} deleted successfully")

            # Delete the file
            self.client.files.delete(file_id)
            logging_module.log_success(f"Assistant with {file_id} deleted successfully")

            # Delete the thread
            self.client.beta.threads.delete(thread_id)
            logging_module.log_success(f"Assistant with {thread_id} deleted successfully")
        except Exception as e:
            logging_module.log_error(f"Error occurred while cleaning up resources!")