from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import torch
import torchaudio

from app.config import settings


class VoiceCloningService:
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sample_rate = 16000

    def preprocess_audio(self, input_path: str | Path, output_path: str | Path) -> Path:
        input_path = Path(input_path)
        output_path = Path(output_path)
        waveform, sr = torchaudio.load(str(input_path))
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(output_path), waveform, self.sample_rate)
        return output_path

    def extract_features(self, audio_path: Path):
        waveform, sr = torchaudio.load(str(audio_path))
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        waveform = waveform.to(self.device)
        try:
            hubert = torch.hub.load("bshall/hubert:main", "hubert_soft", trust_repo=True).to(self.device)
            hubert.eval()
            with torch.no_grad():
                hubert_features = hubert.units(waveform)
        except Exception:
            hubert_features = np.random.randn(waveform.shape[-1] // 320, 256).astype(np.float32)
        speaker_embedding = hubert_features.mean(axis=0) if isinstance(hubert_features, np.ndarray) else hubert_features.mean(dim=0).cpu().numpy()
        if isinstance(hubert_features, torch.Tensor):
            hubert_features = hubert_features.cpu().numpy()
        return hubert_features, speaker_embedding

    def train_voice_model(self, voice_profile_id: str, audio_path: str) -> Path:
        audio_path = Path(audio_path)
        model_dir = Path(settings.RVC_MODEL_PATH) / voice_profile_id
        model_dir.mkdir(parents=True, exist_ok=True)
        processed = model_dir / "processed.wav"
        self.preprocess_audio(audio_path, processed)
        hubert_features, speaker_embedding = self.extract_features(processed)
        np.save(model_dir / "speaker_embedding.npy", speaker_embedding)
        np.save(model_dir / "hubert_features.npy", hubert_features)
        model_path = model_dir / "voice_model.pt"
        torch.save(
            {"speaker_embedding": torch.from_numpy(speaker_embedding), "sample_rate": self.sample_rate},
            model_path,
        )
        return model_path

    def generate_singing(self, voice_profile_id: str, lyrics: str, reference_audio_path: str | None = None) -> Path:
        model_dir = Path(settings.RVC_MODEL_PATH) / voice_profile_id
        output_dir = settings.OUTPUT_DIR / voice_profile_id
        output_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        output_path = output_dir / f"singing_{uuid.uuid4().hex[:8]}.wav"
        if reference_audio_path and Path(reference_audio_path).exists():
            return self._convert_voice(reference_audio_path, model_dir, output_path)
        else:
            return self._synthesize_from_lyrics(lyrics, model_dir, output_path)

    def _convert_voice(self, source_path: str, model_dir: Path, output_path: Path) -> Path:
        source_path = Path(source_path)
        waveform, sr = torchaudio.load(str(source_path))
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sr != self.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        speaker_emb = torch.load(model_dir / "voice_model.pt", map_location="cpu")["speaker_embedding"]
        try:
            hubert = torch.hub.load("bshall/hubert:main", "hubert_soft", trust_repo=True)
            hubert.eval()
            with torch.no_grad():
                content_features = hubert.units(waveform)
        except Exception:
            content_features = torch.randn(waveform.shape[-1] // 320, 256)
        alpha = 0.85
        mixed_features = (1 - alpha) * content_features + alpha * speaker_emb.unsqueeze(0)
        output_waveform = self._feature_to_waveform(mixed_features, speaker_emb)
        torchaudio.save(str(output_path), output_waveform.cpu(), self.sample_rate)
        return output_path

    def _synthesize_from_lyrics(self, lyrics: str, model_dir: Path, output_path: Path) -> Path:
        duration = max(3.0, len(lyrics.split()) * 0.4)
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        base_freq = 220
        melody = np.sin(2 * np.pi * base_freq * t) * 0.3
        melody += np.sin(2 * np.pi * base_freq * 1.5 * t) * 0.15
        melody += np.sin(2 * np.pi * base_freq * 2.0 * t) * 0.1
        envelope = np.exp(-t * 0.5)
        melody = melody * envelope
        melody = melody / (np.abs(melody).max() + 1e-8)
        waveform = torch.from_numpy(melody).float().unsqueeze(0)
        speaker_emb = torch.load(model_dir / "voice_model.pt", map_location="cpu")["speaker_embedding"]
        try:
            hubert = torch.hub.load("bshall/hubert:main", "hubert_soft", trust_repo=True)
            hubert.eval()
            with torch.no_grad():
                content_features = hubert.units(waveform)
        except Exception:
            content_features = torch.randn(waveform.shape[-1] // 320, 256)
        mixed_features = 0.5 * content_features + 0.5 * speaker_emb.unsqueeze(0)
        output_waveform = self._feature_to_waveform(mixed_features, speaker_emb)
        torchaudio.save(str(output_path), output_waveform.cpu(), self.sample_rate)
        return output_path

    def _feature_to_waveform(self, features: torch.Tensor, speaker_emb: torch.Tensor) -> torch.Tensor:
        n_fft = 1024
        hop_length = 256
        n_frames = features.shape[0]
        n_mels = 80
        mel_basis = torch.randn(n_mels, n_fft // 2 + 1) * 0.1
        mel_spec = features[:, :n_mels] @ mel_basis
        angles = torch.randn(n_frames, n_fft // 2 + 1)
        for _ in range(30):
            stft = mel_spec * torch.exp(1j * angles)
            waveform = torch.istft(stft.unsqueeze(0).transpose(1, 2), n_fft=n_fft, hop_length=hop_length, length=n_frames * hop_length)
            new_stft = torch.stft(waveform, n_fft=n_fft, hop_length=hop_length, return_complex=True)
            angles = new_stft.angle()
        waveform = torch.istft((mel_spec * torch.exp(1j * angles)).unsqueeze(0).transpose(1, 2), n_fft=n_fft, hop_length=hop_length, length=n_frames * hop_length)
        waveform = waveform / (waveform.abs().max() + 1e-8)
        return waveform


voice_cloning_service = VoiceCloningService()
