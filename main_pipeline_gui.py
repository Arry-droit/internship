import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

from enhance_audio import main as enhance_main
from enhance_transcribe_tts import run_pipeline

class PipelineApp(TkinterDnD.Tk if DND_AVAILABLE else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Denoise, Transcribe & TTS Pipeline")
        self.geometry("400x340")
        self.resizable(False, False)

        self.file_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=os.getcwd())
        self.accent = tk.StringVar(value="neutral")
        self.enhanced_path = None
        self.tts_path = None

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

        # Output directory selection
        tk.Label(self, text="Output Folder:").pack(pady=(10, 0))
        out_frame = tk.Frame(self)
        out_frame.pack(pady=5)
        self.out_entry = tk.Entry(out_frame, textvariable=self.output_dir, width=35)
        self.out_entry.pack(side=tk.LEFT, padx=(0, 5))
        out_btn = tk.Button(out_frame, text="Select...", command=self.select_output_dir)
        out_btn.pack(side=tk.LEFT)

        # Accent selection
        tk.Label(self, text="Select Accent:").pack(pady=(10, 0))
        accent_combo = ttk.Combobox(self, textvariable=self.accent, values=["neutral", "british", "american"], state="readonly")
        accent_combo.pack(pady=5)

        # Run button
        run_btn = tk.Button(self, text="Run Pipeline", command=self.run_pipeline)
        run_btn.pack(pady=10)

        # Play buttons
        self.play_enhanced_btn = tk.Button(self, text="Play Noise Cancelled", command=self.play_enhanced, state=tk.DISABLED)
        self.play_enhanced_btn.pack(pady=5)
        self.play_tts_btn = tk.Button(self, text="Play Accent Nullified", command=self.play_tts, state=tk.DISABLED)
        self.play_tts_btn.pack(pady=5)

        if not DND_AVAILABLE:
            tk.Label(self, text="(Drag-and-drop disabled: tkinterdnd2 not installed)", fg="red").pack(pady=(0, 5))
        if not PLAYSOUND_AVAILABLE:
            tk.Label(self, text="(Audio playback disabled: playsound not installed)", fg="red").pack(pady=(0, 5))

    def browse_file(self):
        filetypes = [("Audio files", "*.wav *.flac *.mp3"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select Audio File", filetypes=filetypes)
        if filename:
            self.file_path.set(filename)

    def select_output_dir(self):
        dirname = filedialog.askdirectory(title="Select Output Folder")
        if dirname:
            self.output_dir.set(dirname)

    def drop_file(self, event):
        dropped_file = event.data.strip('{}')
        if os.path.isfile(dropped_file):
            self.file_path.set(dropped_file)

    def run_pipeline(self):
        input_path = self.file_path.get()
        accent = self.accent.get()
        output_dir = self.output_dir.get()
        if not os.path.isfile(input_path):
            messagebox.showerror("Error", "Please select a valid audio file.")
            return
        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Please select a valid output folder.")
            return

        try:
            # Denoise
            self.enhanced_path = os.path.join(output_dir, "enhanced.wav")
            sys.argv = ["enhance_audio.py", "--input", input_path]
            import enhance_audio
            original_save_audio = enhance_audio.save_audio
            def save_audio_override(path, audio, sr):
                original_save_audio(self.enhanced_path, audio, sr)
            enhance_audio.save_audio = save_audio_override
            enhance_main()
            enhance_audio.save_audio = original_save_audio  # Restore

            # Transcribe & TTS
            import enhance_transcribe_tts
            original_run_pipeline = enhance_transcribe_tts.run_pipeline
            def run_pipeline_override(accent, input_path):
                transcript_path = os.path.join(output_dir, "transcript.txt")
                self.tts_path = os.path.join(output_dir, f"tts_{accent.lower()}.mp3")
                original_run_pipeline(accent, input_path)
                # Move files if needed
                if os.path.exists("transcript.txt"):
                    os.replace("transcript.txt", transcript_path)
                if os.path.exists(f"tts_{accent.lower()}.mp3"):
                    os.replace(f"tts_{accent.lower()}.mp3", self.tts_path)
            enhance_transcribe_tts.run_pipeline = run_pipeline_override
            run_pipeline(accent=accent, input_path=self.enhanced_path)
            enhance_transcribe_tts.run_pipeline = original_run_pipeline  # Restore

            self.play_enhanced_btn.config(state=tk.NORMAL if PLAYSOUND_AVAILABLE else tk.DISABLED)
            self.play_tts_btn.config(state=tk.NORMAL if PLAYSOUND_AVAILABLE else tk.DISABLED)

            messagebox.showinfo("Success", f"Pipeline complete!\nCheck output files in:\n{output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Pipeline failed:\n{e}")

    def play_enhanced(self):
        if self.enhanced_path and os.path.exists(self.enhanced_path):
            threading.Thread(target=playsound, args=(self.enhanced_path,), daemon=True).start()
        else:
            messagebox.showerror("Error", "Noise cancelled file not found.")

    def play_tts(self):
        # Check for all possible accent TTS files in the output directory
        possible_files = [
            os.path.join(self.output_dir.get(), "tts_neutral.mp3"),
            os.path.join(self.output_dir.get(), "tts_british.mp3"),
            os.path.join(self.output_dir.get(), "tts_american.mp3"),
        ]
        for tts_file in possible_files:
            if os.path.exists(tts_file):
                threading.Thread(target=playsound, args=(tts_file,), daemon=True).start()
                return
        messagebox.showerror("Error", "Accent nullified file not found.")

if __name__ == "__main__":
    app = PipelineApp()
    app.mainloop()