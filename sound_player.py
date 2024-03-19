import simpleaudio as sa
import threading
from queue import Queue

class SoundPlayer:
    def __init__(self):
        self.sounds = {
            "ding": "sound/ding.wav",
            "dong": "sound/dong.wav",
            "gentle_thought": "sound/gentle_thought.wav",
            "memory_erase": "sound/memory_erase.wav",
            "think_hard": "sound/think_hard.wav",
            "startup": "sound/startup.wav"
        }
        self.queue = Queue()
        self.currently_playing = False
        # Start a thread that will handle the sound playing
        self.player_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.player_thread.start()

    def enqueue_sound(self, sound_name):
        """
        Enqueue a sound to be played. This function is non-blocking.
        """
        self.queue.put(sound_name)

    def _process_queue(self):
        while True:
            sound_name = self.queue.get()
            if sound_name in self.sounds:
                self.currently_playing = True
                wave_obj = sa.WaveObject.from_wave_file(self.sounds[sound_name])
                play_obj = wave_obj.play()
                play_obj.wait_done()
                self.currently_playing = False
            else:
                print(f"Sound {sound_name} not found.")
            self.queue.task_done()

    def is_playing(self):
        """
        Check if a sound is currently playing or if there are sounds enqueued.
        """
        return not self.queue.empty() or self.currently_playing
