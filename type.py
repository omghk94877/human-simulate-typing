import threading
import random
import time
import string

import pyautogui
pyautogui.PAUSE = 0

import tkinter as tk
from tkinter import ttk, messagebox

try:
    import keyboard
    has_keyboard = True
except ImportError:
    has_keyboard = False

# Characters that trigger a longer "sentence end" pause
sentence_end_characters = {'.', '!', '?', '\n', '。', '"', '"'}


class TypingSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Human Typing Simulator")

        # insilize the status 
        self.typing_thread = None
        self.is_typing = False
        self.paused = False
        self.stopped = False

        # Settings variables
        self.start_delay_var = tk.DoubleVar(value=3.0)
        self.char_min_var = tk.DoubleVar(value=0.10)
        self.char_max_var = tk.DoubleVar(value=0.28)
        self.sentence_min_var = tk.DoubleVar(value=2.5)
        self.sentence_max_var = tk.DoubleVar(value=7.0)
        self.typo_prob_var = tk.DoubleVar(value=0.04)

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="both", expand=True)

        info_label = ttk.Label(
            top_frame,
            text=(
                "This tool simulates human typing behavior.\n"
                "Configure the settings below and start typing after the delay."
            ),
            wraplength=400
        )
        info_label.pack(anchor="w")

        text_label = ttk.Label(top_frame, text="Text to Type:")
        text_label.pack(anchor="w", pady=(8, 2))

        self.text_box = tk.Text(top_frame, height=8, wrap="word")
        self.text_box.pack(fill="both", expand=True)

        # Typing settings
        settings_frame = ttk.LabelFrame(self.root, text="Typing Pace", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        row = 0
        ttk.Label(settings_frame, text="Seconds pause before start:").grid(row=row, column=0, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.start_delay_var, width=8).grid(row=row, column=1, sticky="w", padx=5)
        ttk.Label(settings_frame, text="(gives you time to switch tabs)").grid(row=row, column=2, sticky="w")

        row += 1
        ttk.Label(settings_frame, text="Character delay (seconds):").grid(row=row, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.char_min_var, width=8).grid(row=row, column=1, sticky="w", padx=2)
        ttk.Label(settings_frame, text="to").grid(row=row, column=2, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.char_max_var, width=8).grid(row=row, column=3, sticky="w", padx=2)
        ttk.Label(settings_frame, text="(recommended 0.09 ~ 0.30)").grid(row=row, column=4, sticky="w")

        row += 1
        ttk.Label(settings_frame, text="Sentence end pause (seconds):").grid(row=row, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.sentence_min_var, width=8).grid(row=row, column=1, sticky="w", padx=2)
        ttk.Label(settings_frame, text="to").grid(row=row, column=2, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.sentence_max_var, width=8).grid(row=row, column=3, sticky="w", padx=2)
        ttk.Label(settings_frame, text="(recommended 2 ~ 8)").grid(row=row, column=4, sticky="w")

        row += 1
        ttk.Label(settings_frame, text="Typo probability:").grid(row=row, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.typo_prob_var, width=8).grid(row=row, column=1, sticky="w", padx=2)
        ttk.Label(settings_frame, text="(e.g., 0.03 = 3%)").grid(row=row, column=2, columnspan=3, sticky="w")

        row += 1
        if has_keyboard:
            hotkey_text = "Hotkeys: Ctrl+Alt+P = Pause/Resume, Ctrl+Alt+L = Stop"
        else:
            hotkey_text = (
                "keyboard module not installed, global hotkeys disabled "
                "(pip install keyboard to enable)"
            )
        ttk.Label(settings_frame, text=hotkey_text, foreground="gray").grid(
            row=row, column=0, columnspan=5, sticky="w", pady=(8, 0)
        )

        # Buttons
        buttons_frame = ttk.Frame(self.root, padding=10)
        buttons_frame.pack(fill="x")

        self.start_button = ttk.Button(buttons_frame, text="Start", command=self.on_start)
        self.start_button.pack(side="left")

        self.pause_button = ttk.Button(buttons_frame, text="Pause", command=self.on_toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.on_stop, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.status_label = ttk.Label(buttons_frame, text="Status: Waiting", foreground="blue")
        self.status_label.pack(side="left", padx=20)

    def send_notification(self, message):
        threading.Thread(target=self._send_notification_impl, args=(message,), daemon=True).start()

    def _send_notification_impl(self, message):
        if hasattr(self, 'use_telegram_var') and HAS_REQUESTS:
            token = getattr(self, 'token', tk.StringVar()).get().strip()
            chatid = getattr(self, 'chatid', tk.StringVar()).get().strip()
            if token and chatid:
                try:
                    import requests
                    url = f""
                    requests.post(url, data={"chat_id": chatid, "text": message})
                except Exception:
                    pass


    def on_start(self):
        if self.is_typing:
            return

        text = self.text_box.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showwarning("Warning", "Text is empty. Please paste some content first.")
            return

        try:
            start_delay = max(0.0, float(self.start_delay_var.get()))
            char_min = float(self.char_min_var.get())
            char_max = float(self.char_max_var.get())
            sent_min = float(self.sentence_min_var.get())
            sent_max = float(self.sentence_max_var.get())
            typo_prob = float(self.typo_prob_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please ensure all numeric fields contain valid numbers.")
            return

        if char_min <= 0 or char_max <= 0 or char_max < char_min:
            messagebox.showerror("Error", "Character delay range is not reasonable.")
            return
        if sent_min <= 0 or sent_max <= 0 or sent_max < sent_min:
            messagebox.showerror("Error", "Sentence end pause range is not reasonable.")
            return
        if not (0.0 <= typo_prob <= 0.5):
            messagebox.showerror("Error", "Typo probability is recommended to be between 0.0 and 0.5.")
            return

        self.is_typing = True
        self.paused = False
        self.stopped = False
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal", text="Pause")
        self.stop_button.config(state="normal")
        self.status_label.config(
            text=f"Status: Typing will start in {start_delay:.1f} seconds. "
                 f"Switch to the target window and click the input box.",
            foreground="green"
        )

        config = {
            "text": text,
            "start_delay": start_delay,
            "char_min": char_min,
            "char_max": char_max,
            "sent_min": sent_min,
            "sent_max": sent_max,
            "typo_prob": typo_prob,
        }
        self.typing_thread = threading.Thread(target=self.type_text, args=(config,), daemon=True)
        self.typing_thread.start()

        if has_keyboard:
            try:
                keyboard.add_hotkey("ctrl+alt+p", self.toggle_pause_hotkey)
                keyboard.add_hotkey("ctrl+alt+l", self.stop_hotkey)
            except Exception:
                pass

    def on_toggle_pause(self):
        if not self.is_typing:
            return
        self.paused = not self.paused
        if self.paused:
            self.status_label.config(text="Status: Paused (Ctrl+Alt+P to resume)", foreground="orange")
            self.pause_button.config(text="Continue")
        else:
            self.status_label.config(text="Status: Typing...", foreground="green")
            self.pause_button.config(text="Pause")

    def on_stop(self):
        if not self.is_typing:
            return
        self.stopped = True
        self.status_label.config(text="Status: Stopping...", foreground="red")

    def toggle_pause_hotkey(self):
        self.root.after(0, self.on_toggle_pause)

    def stop_hotkey(self):
        self.root.after(0, self.on_stop)

    def on_typing_finished(self, interrupted: bool):
        self.is_typing = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")

        if interrupted:
            self.status_label.config(text="Status: Stopped", foreground="red")
        else:
            self.status_label.config(text="Status: Done", foreground="blue")

        if has_keyboard:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass

    def type_text(self, config):
        text = config["text"]
        start_delay = config["start_delay"]
        char_min = config["char_min"]
        char_max = config["char_max"]
        sent_min = config["sent_min"]
        sent_max = config["sent_max"]
        typo_prob = config["typo_prob"]

        if start_delay > 0:
            time.sleep(start_delay)

        if self.stopped:
            self.root.after(0, self.on_typing_finished, True)
            return

        self.root.after(0, lambda: self.status_label.config(text="Status: Typing...", foreground="green"))

        i = 0
        n = len(text)
        interrupted = False

        while i < n:
            if self.stopped:
                interrupted = True
                break

            if self.paused:
                time.sleep(0.1)
                continue

            char = text[i]

            # simulate occasional typo
            if typo_prob > 0 and char.isalnum() and random.random() < typo_prob:
                wrong_char = random.choice(string.ascii_lowercase)
                pyautogui.write(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                pyautogui.press("backspace")

            pyautogui.write(char)
            i += 1

            if char in sentence_end_characters:
                pause_time = random.uniform(sent_min, sent_max)
                time.sleep(pause_time)
            else:
                delay = random.uniform(char_min, char_max)
                time.sleep(delay)

        self.root.after(0, self.on_typing_finished, interrupted)


if __name__ == "__main__":
    root = tk.Tk()
    app = TypingSimulator(root)
    root.mainloop()
