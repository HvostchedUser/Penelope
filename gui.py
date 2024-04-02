import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading

from penelope_system import PenelopeSystem


class PenelopeChatGUI:
    def __init__(self, master):
        self.master = master
        self.penelope_system = PenelopeSystem()
        self.setup_gui()
        # self.update_chat_history()

    def setup_gui(self):
        self.master.title("Penelope Chat")
        self.chat_history_area = ScrolledText(self.master, state='disabled', width=80, height=20)
        self.chat_history_area.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.message_entry = tk.Entry(self.master, width=58)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5, sticky='we')
        self.message_entry.bind("<Return>", lambda event: self.send_message())  # Bind Enter to send_message

        self.send_button = tk.Button(self.master, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=5, pady=5, sticky='e')

    def logprob_to_color(self, logprob, is_thought):
        """Maps a logprob to a discrete color intensity based on confidence level,
           and uses blue color for indicating thinking."""
        if is_thought:
            return "#2222FF"  # Blue for thinking, kept the same for clear distinction

        # Define thresholds for the discrete levels with more readable colors
        thresholds = [(0.0, "#008800"),  # Very High: Darker green
                      (-1.0, "#444400"),  # High: Light green, but less bright
                      (-2.0, "#992200"),  # Low: Orange, less bright
                      (-3.0, "#FF0000")]  # Very Low: Red, more muted

        # Iterate through thresholds to find where logprob falls
        for threshold, color in thresholds:
            if logprob > threshold:
                return color

        # Default to very low confidence color if none match
        return thresholds[-1][1]

    def send_message(self):
        user_message = self.message_entry.get()
        if user_message and not self.send_button['state'] == 'disabled':
            self.chat_history_area.configure(state='normal')

            self.chat_history_area.insert(tk.END, "\n"+user_message+"\n")

            self.chat_history_area.configure(state='disabled')
            self.chat_history_area.see(tk.END)
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

    # def update_chat_history(self):
    #     self.chat_history_area.configure(state='normal')
    #     self.chat_history_area.delete('1.0', tk.END)
    #     self.chat_history_area.insert(tk.END, "".join(self.penelope_system.chat_history))
    #     self.chat_history_area.configure(state='disabled')

    def generate_response(self):
        for token, pondering_intensity, is_thought, logprob in self.penelope_system.generate_response():
            self.chat_history_area.configure(state='normal')
            color = self.logprob_to_color(logprob, is_thought)

            # Tag name based on color. Assuming color determines the tag's unique configuration
            tag_name = f"conf_{color}"

            # Configure tag with the specific foreground color. If the tag already exists,
            # this will simply reapply the existing configuration.
            self.chat_history_area.tag_configure(tag_name, foreground=color)

            # Insert the token with the specified tag
            self.chat_history_area.insert(tk.END, token, tag_name)

            self.chat_history_area.configure(state='disabled')
            self.chat_history_area.see(tk.END)
        # self.update_chat_history()
        self.master.after(0, self.enable_input)


if __name__ == "__main__":
    root = tk.Tk()
    app = PenelopeChatGUI(root)
    root.mainloop()
