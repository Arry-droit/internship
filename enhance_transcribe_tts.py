import argparse
import os
from typing import Tuple

import numpy as np
import torch
import torchaudio

from df.enhance import enhance, init_df, load_audio, save_audio
from df.utils import download_file


def denoise(input_path: str, output_path: str | None = None) -> Tuple[str, int]:
	model, df_state, _ = init_df()
	audio, _ = load_audio(input_path, sr=df_state.sr())
	enhanced_audio = enhance(model, df_state, audio)
	out_path = output_path or os.path.splitext(input_path)[0] + "_enhanced.wav"
	save_audio(out_path, enhanced_audio, df_state.sr())
	return out_path, df_state.sr()


def _to_16k_mono(audio: torch.Tensor, sr: int) -> np.ndarray:
	if audio.dim() == 2:
		# [channels, time] -> mono
		audio = torch.mean(audio, dim=0)
	# ensure shape [time]
	if sr != 16000:
		audio = torchaudio.functional.resample(audio, orig_freq=sr, new_freq=16000)
	return audio.detach().cpu().float().numpy()


def transcribe_whisper_numpy(audio_np_16k: np.ndarray, task: str = "transcribe", language: str | None = None) -> str:
	import whisper  # lazy import to speed startup when not needed

	model = whisper.load_model("base", device="cpu")
	# Prepare features without ffmpeg
	audio_np_16k = whisper.pad_or_trim(audio_np_16k)
	mel = whisper.log_mel_spectrogram(audio_np_16k).to(model.device)

	if task == "translate":
		options = whisper.DecodingOptions(task="translate", language=language)
	else:
		options = whisper.DecodingOptions(task="transcribe", language=language)

	result = whisper.decode(model, mel, options)
	return result.text.strip()


async def tts_edge(text: str, accent: str, out_path: str) -> str:
	# Edge TTS voices: free, no build tools required
	import edge_tts

	accent_lower = accent.lower()
	if accent_lower in {"british", "uk", "gb"}:
		voice = "en-GB-SoniaNeural"
	elif accent_lower in {"american", "us", "usa"}:
		voice = "en-US-JennyNeural"
	else:
		voice = "en-US-AriaNeural"

	communicate = edge_tts.Communicate(text, voice)
	await communicate.save(out_path)
	return out_path


def run_pipeline(accent: str, input_path: str) -> None:
	# 1) Use provided audio
	input_wav = os.path.abspath(input_path)
	if not os.path.exists(input_wav):
		raise FileNotFoundError(f"Input file not found: {input_wav}")

	# 2) Denoise
	enhanced_path, sr = denoise(input_wav, output_path="enhanced.wav")

	# 3) Prepare audio for Whisper without ffmpeg
	audio_tensor, _ = load_audio(enhanced_path, sr=sr)
	audio_np_16k = _to_16k_mono(audio_tensor, sr)

	# 4) Transcribe
	transcript = transcribe_whisper_numpy(audio_np_16k)
	with open("transcript.txt", "w", encoding="utf-8") as f:
		f.write(transcript + "\n")

	# 5) TTS back with accent (MP3 output avoids ffmpeg)
	out_tts = f"tts_{accent.lower()}.mp3"
	import asyncio
	asyncio.run(tts_edge(transcript, accent=accent, out_path=out_tts))

	print("Noise reduction complete -> enhanced.wav")
	print("Transcription saved -> transcript.txt")
	print(f"TTS synthesized with '{accent}' accent -> {out_tts}")


def main() -> None:
	parser = argparse.ArgumentParser(description="Denoise -> Whisper -> Edge TTS pipeline")
	parser.add_argument("--input", required=True, help="Path to input audio file (wav/flac/mp3, etc.)")
	parser.add_argument("--accent", default="neutral", choices=["neutral", "british", "american"], help="Target accent for TTS")
	args = parser.parse_args()
	run_pipeline(accent=args.accent, input_path=args.input)


if __name__ == "__main__":
	main()


