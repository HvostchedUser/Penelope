import random

from llama_cpp import Llama


class Arbiter:
    def __init__(self, model, tie_allowed=True):
        """
        Initializes the Arbiter class with a language model.

        Parameters:
        model (Llama): The language model to use for evaluating the answers.
        tie_allowed (bool): Flag to indicate if ties are allowed in the comparison.
        """
        self.model = model
        self.tie_allowed = tie_allowed

    def compare_answers(self, question, answer1, answer2):
        """
        Compares two answers to a given question and determines which one is better.

        Parameters:
        question (str): The question both answers are responding to.
        answer1 (str): The first answer to compare.
        answer2 (str): The second answer to compare.

        Returns:
        str: The better answer, or 'tie' if they are considered equal and ties are allowed.
        """
        response1 = self.evaluate(question, answer1, answer2)
        response2 = self.evaluate(question, answer2, answer1)

        decision1 = self.parse_decision(response1)
        decision2 = self.parse_decision(response2)

        # Count the results for each answer
        result = decision1-decision2
        print()
        print(f"{decision1}", f"{decision2}", f"{result}")

        if result != 0:
            return result
        elif self.tie_allowed:
            return 0
        else:
            return (answer1 if random.choice([True, False]) else answer2)

    def evaluate(self, question, ans1, ans2):
        """
        Generates a prompt for the model and gets its opinion on which answer is better.

        Parameters:
        question (str): The question to base the evaluation on.
        ans1 (str): First answer.
        ans2 (str): Second answer.

        Returns:
        str: The model's response indicating which answer is better.
        """
        if self.tie_allowed:
            ending_prompt = "At the end, you must state your opinion by writing 'Answer 1', 'Answer 2', or 'tie'."
        else:
            ending_prompt = "At the end, you must state your opinion by writing 'Answer 1' or 'Answer 2'."

        prompt = (f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are an Arbiter, your task is to compare how different LLMs answer the questions and choose the best answer.\n<|eot_id|>\n\n<|start_header_id|>user<|end_header_id|>Given the question: '{question}', which answer is better and why?\n\n"
                  f"Answer 1: {ans1}\n"
                  f"Answer 2: {ans2}\n\n"
                  f"{ending_prompt}\n<|eot_id|>\n\n<|start_header_id|>assistant<|end_header_id|>")

        print()
        print()
        print(prompt)
        print()
        generator = self.model(
            prompt,
            max_tokens=1024,
            stop=["<|eot_id|>"],
            stream=True,
            temperature=0.7,
            top_p=0.9,  # 999999,  # 0.9,
            repeat_penalty=1.25,
            top_k=20,  # 999999,  # 20,
            logprobs=0
        )
        response=""
        for output in generator:
            token_str = output["choices"][0][
                "text"]
            print(token_str, end="")
            response+=token_str
        return response

    def parse_decision(self, text):
        """
        Parses the decision from the model's textual response, using rfind to locate the final decision.

        Parameters:
        text (str): The text output from the model.

        Returns:
        str: The parsed decision ('Answer 1', 'Answer 2', 'tie'), or None if no clear decision.
        """
        # Use rfind to get the last occurrence of each decision
        index1 = text.rfind('Answer 1')
        index2 = text.rfind('Answer 2')
        index_tie = text.rfind('tie') if self.tie_allowed else -1

        # Determine which index is greatest
        max_index = max(index1, index2, index_tie)
        if max_index == index1:
            return -1
        elif max_index == index2:
            return 1
        elif max_index == index_tie:
            return 0
        return None

# Usage of the Arbiter class
model = Llama(
            model_path="/home/ivan/Applications/AI/Models/Meta-Llama-3-8B-Instruct-Q5_K_M.gguf",
            n_ctx=8128,
            n_threads=0,
            n_gpu_layers=0,
            verbose=False,
            n_batch=512,
            logits_all=True,
        )
arbiter = Arbiter(model, tie_allowed=True)
question = "What is the importance of quantum computing in future technologies?"
answer1 = "Quantum computing allows for solving complex problems much faster than classical computers can, which will revolutionize industries."
answer2 = "Quantum computers provide new ways to model molecular interactions, making it a pivotal technology for material science and medicine."

result = arbiter.compare_answers(question, answer1, answer2)
print("The better answer is:", result)
