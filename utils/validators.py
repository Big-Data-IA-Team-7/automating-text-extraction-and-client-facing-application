import json
import tiktoken

def answer_validation_check(final_answer: str, validation_answer: str):
    final_answer = final_answer.strip().lower().replace('"', '')

    if not validation_answer:
        return None

    validation_answer = validation_answer.strip().lower()

    if validation_answer.isdigit():
        final_list = final_answer.split()
        return 1 if validation_answer not in final_list else 2
    else:
        return 1 if validation_answer not in final_answer else 2

def extract_json_contents(file_path):
    with open(file_path, 'r') as file:
        # Load the JSON data
        data = json.load(file)

    # Convert the JSON data to a formatted string
    json_string = json.dumps(data, indent=4)
    
    return json_string

def extract_txt_contents(file_path):
    with open(file_path, 'r') as file:
        # Read the entire content of the file into a string
        file_content = file.read()

        return file_content

def num_tokens_from_string(question_contents: str, model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(question_contents))
    return num_tokens
