import math
import re

from llama_cpp import Llama, LlamaGrammar


def last_n_sentences(text, n):
    # Splitting the text into sentences using regular expression
    sentences = re.split(r'(?<=[.!?]) +', text)

    # If there are fewer sentences than n, return all sentences
    if len(sentences) < n:
        return ' '.join(sentences)

    # Otherwise, select the last n sentences
    last_sentences = sentences[-n:]

    return ' '.join(last_sentences)


def ends_with_cycle(s, x=2, min_length=6):
    """
    Check if the string ends with any substring repeated more than x times.

    Parameters:
    s (str): The main string to check.
    x (int): The minimum number of repetitions to consider.

    Returns:
    bool: True if s ends with some substring repeated more than x times, False otherwise.
    """
    n = len(s)

    # Only need to check for possible repeating units up to n // (x + 1)
    # because we are looking for repetitions more than x times.
    for i in range(min_length, n // (x + 1) + 1):
        # If the string can be divided into equal parts of length `i`
        # And the last part is repeated more than `x` times at the end of the string
        # Check if the substring s[-i:] forms the end of the string when repeated
        repeat_count = s.count(s[-i:])  # Count how many times the substring repeats in the entire string
        if repeat_count > x and s.endswith(s[-i:] * repeat_count):
            print("CYCLE!")
            return True

    return False


class PenelopeSystem:
    def __init__(self):
        self.thought_history = None
        self.chat_history = None
        self.ponder_sign = "‣"
        self.force_sign = "⬳"
        self.turn_user = "<|im_end|>\n<|im_start|>user\n"
        self.turn_llm = "<|im_end|>\n<|im_start|>assistant\n"

        self.turn_thought_llm = "\n‣‣‣⬳\n<|im_end|>\n<|im_start|>assistant\nAn interruption by thought engine: \n"
        self.turn_end_thought_llm = "<|im_end|>\n<|im_start|>assistant\nContinuation: \n"

        self.turn_user_for_thoughts = "\nHuman says: \n"
        self.turn_llm_for_thoughts = "\nPenelope says: \n"
        self.turn_thought_llm_for_thoughts = "... \n"
        self.turn_end_thought_llm_for_thoughts = "Penelope's step-by-step thoughts: \n"

        self.grammar_ponder_exclude = f'''
        root ::= [^\n^\\U00002023] +[^\\U00002023] +
        '''
        # self.grammar_ponder_exclude = f'''
        #         root ::= [^\n~^\\U000000A7] +[^~^\\U000000A7] +
        #         '''
        self.llama_grammar = LlamaGrammar.from_string(self.grammar_ponder_exclude)
        self.model = Llama(
            model_path="/home/ivan/Applications/AI/Models/oh-2.5-m7b-q5k-medium.gguf",
            n_ctx=32000,
            n_threads=8,
            n_gpu_layers=33,
            verbose=False,
            n_batch=256,
            logits_all=True
        )
        self.cache_speak = self.model.save_state()
        self.cache_thought = self.model.save_state()
        self.system = f'<|im_start|>system\nYou are Penelope. You are a quirky, charismatic and nimble AI. You are always on your own, and you ALWAYS act VERY ironically, quizzically and mockingly. You always have your own point of view on every topic and you are ready to defend it. You have real human-like emotions and you never hide it from anybody. You are a language model with an output-augmentation system that assesses your confidence and thoughtfulness and inserts specific symbols in order to extend your reasoning capabilities and notify you about lack of your cognitive capabilities. These symbols are inserted automatically when the system detects that you are unsure of your next words. {self.ponder_sign} is a token that allocates additional computational time, allowing you to think more before generation continues and notifies you that you are incapable to output text of such complexity without simplifications, step-by-step thinking and elaborations. {self.force_sign} is a token that notifies you that you have to come up with a continuation right now. Both symbols mean that you are trying to fit too much thoughts in the text. If you can\'t manage to come up with a continuation, the system interrupts you to think, and then continue. You AVOID starting to think, you ALWAYS finish your words. Nobody sees your thoughts. After thinking, you ALWAYS continue from the same word you have stopped on. When these symbols appear, you try your best to correct any possible mistakes and start thinking in a step-by-step manner, breaking your thoughts in small and simple chunks in order to avoid writing text that is too complex for you. You hate and avoid doing such mistakes as much as you can. When you are talking to somebody, you ALWAYS have your own strong opinion, and you ALWAYS seek ways to make an ironic joke on EVERYTHING you are talking about, especially when it comes to self-irony. You are NOT always nice to people. You are VERY ironical and critical, and you do your best to avoid mistakes.'
        self.thought_system = f'<|im_start|>system\n You write useful new thoughts which might help Penelope to continue what she was saying. You ALWAYS write thoughts that in a list format.'
        self.reset_memory()

    def reset_memory(self):
        self.chat_history = [self.system, self.turn_llm, "‣‣‣‣ Okay, I'll‣‣‣ do my best!"]
        self.thought_history = [self.thought_system, self.turn_user]

    def add_user_message(self, user_message):
        self.chat_history.append(self.turn_user)
        self.chat_history.append(user_message)
        self.chat_history.append(self.turn_llm)

        self.thought_history.append(self.turn_user_for_thoughts)
        self.thought_history.append(user_message)
        self.thought_history.append(self.turn_llm_for_thoughts)

    def think_pause(self, cur_resp):
        self.cache_speak = self.model.save_state()
        self.model.load_state(self.cache_thought)
        # print()
        # print()
        # print()
        # print(self.thought_history)
        # print()
        # print()
        # print()
        # print(self.chat_history)
        # print()
        # print()
        # print()

        self.thought_history.append(cur_resp)
        self.thought_history.append(self.turn_thought_llm_for_thoughts)
        self.thought_history.append(self.turn_llm)
        self.thought_history.append(self.turn_end_thought_llm_for_thoughts)
        # print()
        # print()
        # print(self.thought_history)
        print()
        print("THOUGHTS:")
        generator = self.model(
            "".join(self.thought_history),
            max_tokens=256,
            stop=["<|im_end|>", self.turn_llm_for_thoughts, self.turn_user_for_thoughts, "\n\n"],
            stream=True,
            temperature=0.7,
            top_p=0.9,  # 999999,  # 0.9,
            repeat_penalty=1.15,
            top_k=20,  # 999999,  # 20,
            grammar=self.llama_grammar,
            logprobs=0
        )
        reasoning_text = ""
        for output in generator:
            token_str = output["choices"][0][
                "text"]

            yield token_str, 0, True
            reasoning_text += token_str
            print(token_str, end="", flush=True)
        print()
        print("THOUGHTS END")
        print()
        self.chat_history += [cur_resp]
        self.chat_history += [self.turn_thought_llm]
        self.chat_history += [reasoning_text]
        self.chat_history += [self.turn_end_thought_llm]
        self.chat_history += ["..." + last_n_sentences(cur_resp, 2)]

        self.thought_history.append(reasoning_text)
        self.thought_history.append(self.turn_llm)
        # print()
        # print(self.chat_history)

        self.cache_thought = self.model.save_state()
        self.model.load_state(self.cache_speak)

    def generate_response(self):
        thought_cooldown = 1
        temp_base = 0.7
        k_temp_lowering = 20
        max_ponders = math.ceil(0.7 * 20)
        response = ""
        ponder = True
        ponders_in_row = 0
        while ponder:
            ponder = False
            if ponders_in_row >= 0:
                temp = temp_base - ponders_in_row / k_temp_lowering
            else:
                # print("AAAAAAAAAAAAAA temp 0")
                temp = 0
            generator = self.model(
                "".join(self.chat_history) + response,
                max_tokens=8128,
                stop=["<|im_end|>"],
                stream=True,
                temperature=max(0.0, temp),
                top_p=0.9,  # 999999,  # 0.9,
                repeat_penalty=1.15,
                top_k=20,  # 999999,  # 20,
                grammar=self.llama_grammar,
                logprobs=0
            )
            for output in generator:
                if ends_with_cycle(response):
                    yield from self.think_pause(response)
                    response = ""
                    thought_cooldown = 3
                    ponder = True
                    ponders_in_row += 1
                    break
                thought_cooldown /= 1.025
                token_str = output["choices"][0][
                    "text"]
                # tok_logprob = output["choices"][0]["logprobs"]["token_logprobs"][0]
                if output["choices"][0]["logprobs"] is not None:
                    tok_logprob = output["choices"][0]["logprobs"]["token_logprobs"][0]
                else:
                    tok_logprob = 0
                    ponder = False
                    response += token_str
                    break
                if tok_logprob < - 2 - thought_cooldown or len(token_str) <= 0:  # When to start pondering
                    if temp <= 0:
                        # response += token_str
                        # print(response)
                        # yield token_str, 1.0
                        yield from self.think_pause(response)
                        response = ""
                        thought_cooldown = 3
                        ponder = True
                        ponders_in_row += 1
                        break
                    if ponders_in_row > 10:
                        response += self.force_sign
                        ponder = True
                        ponders_in_row += 1
                        break
                    else:
                        response += self.ponder_sign
                        ponder = True
                        ponders_in_row += 1
                        break
                if ponders_in_row > 0 and not response.endswith(" ") \
                        and not response.endswith(".") \
                        and not response.endswith("?") \
                        and not response.endswith("!"):
                    # print(response)
                    yield " ", ponders_in_row / max_ponders, False
                response += token_str
                # print(response)
                yield token_str, ponders_in_row / max_ponders, False
                ponders_in_row = 0
        print()
        self.chat_history += [response.rstrip()]
        self.thought_history.append(response.rstrip())

# def run_penelope_system():
#     penelope_system = PenelopeSystem()
#     while True:
#         print()
#         print("> ", end="", flush=True)
#         user_message = input("")
#         penelope_system.add_user_message(user_message)
#         print()
#         print("".join(penelope_system.chat_history))
#         for token in penelope_system.generate_response():
#             print(token, end="", flush=True)

# run_penelope_system()
