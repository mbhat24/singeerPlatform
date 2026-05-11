---
title: Singer Platform API
emoji: 🎤
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# Singer Platform - Voice Cloning API

GPU-powered voice cloning API for the Singer Platform. Lets anyone sing in their own voice.

## Features

- **Voice Training**: Upload voice samples, train a custom RVC voice model
- **Singing Generation**: Convert reference audio or synthesize from lyrics in your cloned voice
- **GPU Accelerated**: Runs on T4 GPU for fast inference

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Get current user |
| GET | `/api/voices/` | List voice profiles |
| POST | `/api/voices/upload` | Upload voice sample + train model |
| GET | `/api/voices/{id}` | Get voice profile |
| DELETE | `/api/voices/{id}` | Delete voice profile |
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create singing project |
| GET | `/api/projects/{id}/download` | Download generated audio |
| GET | `/api/health` | Health check + GPU status |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Auto-generated |

## Local Development

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
```
