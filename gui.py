import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading

from penelope_system import PenelopeSystem


class PenelopeChatGUI:
    def __init__(self, master):
        self.master = master
        self.penelope_system = PenelopeSystem()
        self.setup_gui()
        self.update_chat_history()

    def setup_gui(self):
        self.master.title("Penelope Chat")
        self.chat_history_area = ScrolledText(self.master, state='disabled', width=80, height=20)
        self.chat_history_area.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.message_entry = tk.Entry(self.master, width=58)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5, sticky='we')
        self.message_entry.bind("<Return>", lambda event: self.send_message())  # Bind Enter to send_message

        self.send_button = tk.Button(self.master, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=5, pady=5, sticky='e')

    def logprob_to_color(self, logprob):
        """Maps a logprob to a color intensity in a continuous manner."""
        # Assuming logprob ranges from -3 (low confidence) to 0 (high confidence)
        min_logprob, max_logprob = -3.0, 0.0
        # Normalize logprob to a 0-1 range
        normalized = (logprob - min_logprob) / (max_logprob - min_logprob)
        normalized = max(0, min(1, normalized))  # Clamp to [0, 1] range

        # Linear interpolation between red (low confidence) and green (high confidence)
        red_intensity = int(255 * (1 - normalized))
        green_intensity = int(255 * normalized)
        color = f'#{red_intensity:02x}{green_intensity:02x}00'
        return color

    def send_message(self):
        user_message = self.message_entry.get()
        if user_message and not self.send_button['state'] == 'disabled':
            self.penelope_system.add_user_message(user_message)
            self.message_entry.delete(0, tk.END)
            self.disable_input()
            threading.Thread(target=self.generate_response).start()

    def disable_input(self):
        """Disable the message entry and send button."""
        self.message_entry.configure(state='disabled')
        self.send_button.configure(state='disabled')

    def enable_input(self):
        """Re-enable the message entry and send button."""
        self.message_entry.configure(state='normal')
        self.send_button.configure(state='normal')

    def update_chat_history(self):
        self.chat_history_area.configure(state='normal')
        self.chat_history_area.delete('1.0', tk.END)
        self.chat_history_area.insert(tk.END, "".join(self.penelope_system.chat_history))
        self.chat_history_area.configure(state='disabled')

    def generate_response(self):
        for token, pondering_intensity, is_thought, logprob in self.penelope_system.generate_response():
            self.chat_history_area.configure(state='normal')
            color = self.logprob_to_color(logprob)
            tag_name = f"logprob_{color}"
            self.chat_history_area.tag_configure(tag_name, foreground=color)
            self.chat_history_area.insert(tk.END, token, tag_name)
            self.chat_history_area.configure(state='disabled')
            self.chat_history_area.see(tk.END)
        self.update_chat_history()
        self.master.after(0, self.enable_input)

if __name__ == "__main__":
    root = tk.Tk()
    app = PenelopeChatGUI(root)
    root.mainloop()
