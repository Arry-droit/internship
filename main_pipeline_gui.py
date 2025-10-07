import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from enhance_audio import main as enhance_main
from enhance_transcribe_tts import run_pipeline

class PipelineApp(TkinterDnD.Tk if DND_AVAILABLE else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Denoise, Transcribe & TTS Pipeline")
        self.geometry("400x220")
        self.resizable(False, False)

        self.file_path = tk.StringVar()
        self.accent = tk.StringVar(value="neutral")

        # File selection
        tk.Label(self, text="Input Audio File:").pack(pady=(15, 0))
        file_frame = tk.Frame(self)
        file_frame.pack(pady=5)
        if DND_AVAILABLE:
            self.file_entry = tk.Entry(file_frame, textvariable=self.file_path, width=35)
            self.file_entry.pack(side=tk.LEFT, padx=(0, 5))
            self.file_entry.drop_target_register(DND_FILES)
            self.file_entry.dnd_bind('<<Drop>>', self.drop_file)
        else:
            self.file_entry = tk.Entry(file_frame, textvariable=self.file_path, width=35)
            self.file_entry.pack(side=tk.LEFT, padx=(0, 5))
        browse_btn = tk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT)

        # Accent selection
        tk.Label(self, text="Select Accent:").pack(pady=(15, 0))
        accent_combo = ttk.Combobox(self, textvariable=self.accent, values=["neutral", "british", "american"], state="readonly")
        accent_combo.pack(pady=5)

        # Run button
        run_btn = tk.Button(self, text="Run Pipeline", command=self.run_pipeline)
        run_btn.pack(pady=20)

        if not DND_AVAILABLE:
            tk.Label(self, text="(Drag-and-drop disabled: tkinterdnd2 not installed)", fg="red").pack(pady=(0, 5))

    def browse_file(self):
        filetypes = [("Audio files", "*.wav *.flac *.mp3"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Audio File", filetypes=filetypes)
        if filename:
            self.file_path.set(filename)

    def drop_file(self, event):
        dropped_file = event.data.strip('{}')
        if os.path.isfile(dropped_file):
            self.file_path.set(dropped_file)

    def run_pipeline(self):
        input_path = self.file_path.get()
        accent = self.accent.get()
        if not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid audio file.")
            return

        try:
            sys.argv = ["enhance_audio.py", "--input", input_path]
            enhance_main()
            enhanced_path = os.path.abspath("enhanced.wav")
            run_pipeline(accent=accent, input_path=enhanced_path)
            messagebox.showinfo("Success", "Pipeline complete!\nCheck enhanced.wav, transcript.txt, and TTS output.")
        except Exception as e:
            messagebox.showerror("Error", f"Pipeline failed:\n{e}")

if __name__ == "__main__":
    app = PipelineApp()
    app.mainloop()