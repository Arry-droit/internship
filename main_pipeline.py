import sys
import os

from enhance_audio import main as enhance_main
from enhance_transcribe_tts import run_pipeline

def main():
    # Prompt user for input path
    input_path = input("Enter the path to your input audio file: ").strip()
    while not os.path.isfile(input_path):
        print("File not found. Please enter a valid file path.")
        input_path = input("Enter the path to your input audio file: ").strip()

    # Prompt user for accent selection
    accent_options = ["neutral", "british", "american"]
    print("Select accent for TTS:")
    for idx, option in enumerate(accent_options, 1):
        print(f"{idx}. {option.capitalize()}")
    accent_choice = input("Enter the number of your choice (1-3): ").strip()
    while accent_choice not in {"1", "2", "3"}:
        print("Invalid choice. Please enter 1, 2, or 3.")
        accent_choice = input("Enter the number of your choice (1-3): ").strip()
    accent = accent_options[int(accent_choice) - 1]

    # Step 1: Denoise audio
    sys.argv = ["enhance_audio.py", "--input", input_path]
    enhance_main()

    # Step 2: Transcribe and TTS
    enhanced_path = os.path.abspath("enhanced.wav")
    run_pipeline(accent=accent, input_path=enhanced_path)

if __name__ == "__main__":
    main()