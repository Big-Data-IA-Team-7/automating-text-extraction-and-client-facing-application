import json

def answer_validation_check(final_answer: str, validation_answer: str):
    final_answer = final_answer.strip().lower()

    if not validation_answer:
        return None

    validation_answer = validation_answer.strip().lower().replace('`', '')

    if final_answer.isdigit():
        validation_list = validation_answer.split()
        return 1 if final_answer not in validation_list else 2
    else:
        return 1 if final_answer not in validation_answer else 2

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