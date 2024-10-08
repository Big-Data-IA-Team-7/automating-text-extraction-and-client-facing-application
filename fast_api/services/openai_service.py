# This Python script defines the OpenAIClient class for interacting with the OpenAI API.
# It initializes the OpenAI client and sets up system prompt instructions for handling different types
# of questions and output formats. The class serves as a wrapper around the OpenAI API, providing a 
# structured way to initialize and manage AI prompts and responses within the application.

import openai
from openai import OpenAI
from project_logging import logging_module

class OpenAIClient:
    def __init__(self):
        """
        Initializes the OpenAIClient with all system prompts.
        """
        self.client = OpenAI()  # Initialize OpenAI client

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
