from __future__ import annotations

from pathlib import Path

from pydub import AudioSegment


def convert_to_wav(input_path: str | Path, output_path: str | Path) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    audio = AudioSegment.from_file(str(input_path))
    audio = audio.set_frame_rate(16000).set_channels(1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(output_path), format="wav")
    return output_path


def get_audio_duration(path: str | Path) -> float:
    audio = AudioSegment.from_file(str(path))
    return len(audio) / 1000.0


def trim_silence(input_path: str | Path, output_path: str | Path, threshold_db: int = -40) -> Path:
    audio = AudioSegment.from_file(str(input_path))
    trimmed = audio.strip_silence(silence_thresh=threshold_db)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    trimmed.export(str(output_path), format="wav")
    return output_path
