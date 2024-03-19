import asyncio
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

class VoiceRecognizer:
    def __init__(self, model_type="base", language="en", blocksize=4096, silence_threshold=500, min_silence_length=0.8, synthesizer=None):
        print("Loading Whisper model...")
        self.model = WhisperModel(model_type)
        self.language = language
        self.blocksize = blocksize
        self.silence_threshold = silence_threshold
        self.min_silence_length = min_silence_length
        self.synthesizer = synthesizer
        self._reset()

    def _reset(self):
        # Initialize as a 2D array to match the shape of 'indata'
        self.global_ndarray = np.empty((0,1), dtype=np.int16)
        self.last_sound_time = None
        self.currently_silent = True

    async def inputstream_generator(self):
        q_in = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def callback(indata, frame_count, time_info, status):
            if self.synthesizer and not self.synthesizer.currently_speaking():
                loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))
            elif not self.synthesizer:
                loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

        stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=self.blocksize, callback=callback)
        with stream:
            while True:
                indata, status = await q_in.get()
                yield indata, status

    def _is_silence(self, indata):
        amplitude = np.abs(indata).mean()
        return amplitude < self.silence_threshold

    async def process_audio_buffer(self, on_transcription):
        print("[INFO] Starting voice recognition...")

        SAMPLE_RATE = 16000  # Whisper models expect a sample rate of 16 kHz

        async for indata, status in self.inputstream_generator():
            silence = self._is_silence(indata)

            if silence and self.currently_silent:
                continue

            current_time = asyncio.get_event_loop().time()

            if not silence:
                self.last_sound_time = current_time
                self.currently_silent = False
                self.global_ndarray = np.concatenate((self.global_ndarray, indata), axis=0)
            elif not self.currently_silent and (current_time - self.last_sound_time) >= self.min_silence_length:
                print("[INFO] End of sentence detected. Transcribing...")
                self.currently_silent = True
                # Ensure the audio data is a 1D array before transformation
                indata_transformed = self.global_ndarray.flatten().astype(np.float32) / 32768.0
                # Check the length of the audio; if too long, consider trimming or splitting
                if len(indata_transformed) > SAMPLE_RATE * 30:  # Limit to 30 seconds of audio
                    indata_transformed = indata_transformed[-SAMPLE_RATE * 30:]
                try:
                    result, _ = self.model.transcribe(indata_transformed, language=self.language)
                    text = " ".join(segment.text for segment in result)
                    print(f"[INFO] Transcription result: {text}")
                    on_transcription(text)
                except Exception as e:
                    print(f"[ERROR] Transcription error: {e}")
                self._reset()
