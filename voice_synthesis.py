import io
import wave
import threading
from pathlib import Path
from queue import Queue, Empty
from time import sleep

import simpleaudio as sa

from typing import Dict, Any
from piper import PiperVoice
from piper.download import ensure_voice_exists, find_voice, get_voices

class SpeechSynthesizer:
    def __init__(self, model: str = "en_GB-alba-medium", data_dir: str = ".", download_dir: str = ".", update_voices: bool = True, use_cuda: bool = False):
        self.model = model
        self.data_dir = data_dir
        self.download_dir = download_dir
        self.update_voices = update_voices
        self.use_cuda = use_cuda
        self.text_queue = Queue()
        self.audio_queue = Queue()
        self.is_playing = False
        self.is_computing = False
        self.synthesis_thread = threading.Thread(target=self._synthesize_text, daemon=True)
        self.playback_thread = threading.Thread(target=self._play_audio, daemon=True)
        self.synthesis_thread.start()
        self.playback_thread.start()
        self.voice = self._load_voice()

    def _load_voice(self):
        model_path = Path(self.model)
        if not model_path.exists():
            voices_info = get_voices(self.download_dir, update_voices=self.update_voices)
            aliases_info: Dict[str, Any] = {}
            for voice_info in voices_info.values():
                for voice_alias in voice_info.get("aliases", []):
                    aliases_info[voice_alias] = {"_is_alias": True, **voice_info}
            voices_info.update(aliases_info)
            ensure_voice_exists(self.model, self.data_dir, self.download_dir, voices_info)
            self.model, _ = find_voice(self.model, self.data_dir)
        return PiperVoice.load(self.model, config_path=None, use_cuda=self.use_cuda)

    def enqueue_text(self, text: str):
        self.text_queue.put(text)

    def _synthesize_text(self):
        synthesize_args = {
            "speaker_id": None,
            "length_scale": 1.2,
            "noise_scale": 1.0,
            "noise_w": 1.2,
            "sentence_silence": 0.1,
        }
        while True:
            try:
                text = self.text_queue.get(block=True)
                self.is_computing = True
                with io.BytesIO() as wav_io:
                    with wave.open(wav_io, "wb") as wav_file:
                        self.voice.synthesize(text, wav_file, **synthesize_args)
                    wav_io.seek(0)
                    audio_data = wav_io.read()
                self.audio_queue.put(audio_data)
                self.text_queue.task_done()
                self.is_computing = False
            except Empty:
                self.is_computing = False
                sleep(0.1)
                continue

    def _play_audio(self):
        while True:
            try:
                audio_data = self.audio_queue.get(block=True)
                self.is_playing = True
                with wave.open(io.BytesIO(audio_data), 'rb') as wav:
                    channels = wav.getnchannels()
                    sample_width = wav.getsampwidth()
                    # framerate = wav.getframerate()
                    framerate = 24000
                    play_obj = sa.play_buffer(audio_data, channels, sample_width, framerate)
                    play_obj.wait_done()
                self.audio_queue.task_done()
                self.is_playing = False
            except Empty:
                self.is_playing = False
                sleep(0.1)
                continue

    def currently_speaking(self):
        return self.is_playing or self.is_computing or self.audio_queue.qsize()+self.text_queue.qsize() > 0


# Usage example:
# synthesizer = SpeechSynthesizer()
# synthesizer.enqueue_text("Hello! How are you?")
# synthesizer.enqueue_text("I am fine, thanks!")
# synthesizer.enqueue_text("When trying to using Piper to generate a long tts message (on Sonos speakers, in my case), the audio never plays on the speaker. This seems to happen at around 35 seconds, for me. Anything shorter than that works fine.")

# Check if it is currently speaking
# print(synthesizer.currently_speaking())

# Wait for the queues to be processed
# synthesizer.text_queue.join()
# synthesizer.audio_queue.join()
