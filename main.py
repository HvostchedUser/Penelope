import asyncio
import random
import string
from time import sleep

from sound_player import SoundPlayer
from penelope_system import PenelopeSystem
from voice_recognition import VoiceRecognizer
from voice_synthesis import SpeechSynthesizer

placeholder_tools = [
    "—",
]
placeholder_words = [
    ', am,',
    ', um,',
    ', well,',
    ", erh,",
    # ", Uhhhhhhhhmmmm,",
    # ", Ammmmmmmmmmmm,",
    # ", Hummmmmmmmmmm,",
    # ", Errrhhhhhh,",
    # ", Well,",
]
sounds = SoundPlayer()
print("Load Penelope...")
penelope_system = PenelopeSystem()
print("Load Speech Synthesis...")
synthesizer = SpeechSynthesizer()


def on_transcription_callback(text):
    text = text.replace("penny", "Penni")
    text = text.replace("penelope", "Penelope")
    text = text.replace("panelope", "Penelope")
    text = text.replace("Benny", "Penni")
    text = text.replace("Penny", "Penni")
    text = text.replace("Fanny", "Penni")
    text = text.replace("Glennie", "Penni")
    text = text.replace("Vanellope", "Penelope")
    text = text.replace("Benelope", "Penelope")
    text = text.replace("Manalope", "Penelope")
    text = text.replace("Comand", "command")
    com_rec = " ".join(text.translate(str.maketrans('', '', string.punctuation)).replace("  ", " ").split()).lower()
    if com_rec.endswith("command reset memory"):
        sounds.enqueue_sound("memory_erase")
        penelope_system.reset_memory()
        return
    if not "Penelope" in text and not "Penni" in text:
        return
    sounds.enqueue_sound("dong")
    sounds.enqueue_sound("gentle_thought")
    penelope_system.add_user_message(text)
    text_queue = ""
    for token, ponder_k, is_thinking in penelope_system.generate_response():
        if not sounds.is_playing():
            if not is_thinking:
                sounds.enqueue_sound("gentle_thought")
            else:
                sounds.enqueue_sound("think_hard")

        if is_thinking:
            continue

        if ponder_k > 0.9 and not text_queue.endswith(",") and not text_queue.endswith(
                ", ") and not text_queue.endswith("— "):
            random_word = random.choice(placeholder_words)
            text_queue += random_word
            print(random_word, end="", flush=True)
        elif ponder_k > 0.3 and not text_queue.endswith(",") and not text_queue.endswith(
                ", ") and not text_queue.endswith("— "):
            random_word = random.choice(placeholder_tools)
            text_queue += random_word
            print(random_word, end="", flush=True)
        text_queue += token
        print(token, end="", flush=True)
        if (text_queue.endswith(".") or text_queue.endswith("!") or text_queue.endswith("?")):
            synthesizer.enqueue_text(text_queue)
            print()
            print("* enqueued")
            print()
            text_queue = ""
        if (text_queue.endswith(",")) and synthesizer.audio_queue.qsize() + synthesizer.text_queue.qsize() < 1:
            synthesizer.enqueue_text(text_queue)
            print()
            print("* enqueued")
            print()
            text_queue = ""

    synthesizer.enqueue_text(text_queue)
    while synthesizer.currently_speaking():
        sleep(0.1)
    sounds.enqueue_sound("ding")


print("Load Speech Recognition...")
processor = VoiceRecognizer("Systran/faster-distil-whisper-medium.en", "en", 2048, 50, 0.8, synthesizer)

sounds.enqueue_sound("startup")
asyncio.run(processor.process_audio_buffer(on_transcription_callback))
