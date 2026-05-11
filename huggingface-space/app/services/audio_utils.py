from __future__ import annotations

from pathlib import Path

from pydub import AudioSegment


def convert_to_wav(input_path: str | Path, output_path: str | Path) -> Path:
    audio = AudioSegment.from_file(str(input_path))
    audio = audio.set_frame_rate(16000).set_channels(1)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(output_path), format="wav")
    return output_path


def get_audio_duration(path: str | Path) -> float:
    audio = AudioSegment.from_file(str(path))
    return len(audio) / 1000.0


def trim_silence(path: str | Path, threshold_db: float = -40.0) -> Path:
    audio = AudioSegment.from_file(str(path))
    trimmed = audio.strip_silence(silence_thresh=threshold_db)
    output_path = Path(str(path).replace(".", "_trimmed."))
    trimmed.export(str(output_path), format="wav")
    return output_path
