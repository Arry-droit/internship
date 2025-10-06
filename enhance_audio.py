import argparse
import torchaudio
torchaudio.set_audio_backend("soundfile")

from df.enhance import enhance, init_df, load_audio, save_audio


def main() -> None:
	parser = argparse.ArgumentParser(description="Denoise an input audio file using DeepFilterNet")
	parser.add_argument("--input", required=False, default=r"C:\\Users\\arrys\\Documents\\codes\\internship\\og.wav", help="Path to input audio file (default: C:\\Users\\arrys\\Documents\\codes\\internship\\og.wav)")
	args = parser.parse_args()

	model, df_state, _ = init_df()
	audio, _ = load_audio(args.input, sr=df_state.sr())
	enhanced_audio = enhance(model, df_state, audio)
	save_audio("enhanced.wav", enhanced_audio, df_state.sr())

	print("Noise reduction complete! Check the file: enhanced.wav")


if __name__ == "__main__":
	main()



