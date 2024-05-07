import json
from penelope_system import PenelopeSystem


def answer_questions(input_file, output_file, penelope_s):
    # Load the dataset with questions
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Initialize Penelope system
    penelope = PenelopeSystem()

    # Prepare a list to store answers
    answers = []
    data = data[:100]
    # Process each question
    for item in data:
        penelope.reset_memory()
        question = item['question']

        print(question)
        print()
        print()

        # Simulate dialogue interaction for question-answering
        penelope.add_user_message(question)  # Add the question to the dialogue
        if not penelope_s:
            generator_response = penelope.generate_response_plain()  # Generate the system's response
        else:
            generator_response = penelope.generate_response()  # Generate the system's response

        answer = ""
        # Since response is a generator, consume it into a list
        for token, pondering_intensity, is_thought, logprob in generator_response:
            answer+=token
            print(token, end="")

        print(answer)
        print()
        print()
        print()
        print()
        answers.append({
            "question": question,
            "answer": answer,
            "source": item['source']
        })

        # Save the answers to a new JSON file
        with open(output_file, 'w') as file:
            json.dump(answers, file, indent=4)


# Usage
input_file_path = 'custom_evaluation_dataset.json'  # Path to the JSON file with questions
output_file_path = 'answers_thoughts_100.json'  # Path to the JSON file to save answers

answer_questions(input_file_path, output_file_path, penelope_s = True)

# Usage
input_file_path = 'custom_evaluation_dataset.json'  # Path to the JSON file with questions
output_file_path = 'answers_no_thoughts_100.json'  # Path to the JSON file to save answers

answer_questions(input_file_path, output_file_path, penelope_s = False)