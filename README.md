<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/FFmpeg-7.0+-green?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

<h1 align="center">🎬 Gen Scene Studio Backend</h1>

<p align="center">
  <strong>AI-Powered Video Generation Platform for Shorts & Reels</strong>
</p>

<p align="center">
  Create viral short-form videos for TikTok, Instagram Reels, and YouTube Shorts using cutting-edge AI models.
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎬 **7 AI Video Models** | From economic to premium, choose the right model for your needs |
| 📐 **9:16 Optimized** | Default vertical format for TikTok, Reels & Shorts |
| ⚡ **Async Workers** | Enterprise-grade job processing with concurrent workers |
| 🎨 **Smart Model Selection** | Auto-selects the best AI model based on your chosen style |
| 💾 **Job Persistence** | SQLite database with full job tracking & recovery |
| 🔐 **API Security** | API key authentication with rate limiting |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- FFmpeg 7.0+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/Juanfer85/gen-scene-studio-backend.git
cd gen-scene-studio-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Run Development Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker

```bash
docker compose up -d --build
```

---

## 🎨 Video Models

| Model | Tier | Credits/5s | Best For |
|-------|------|------------|----------|
| **Wan Turbo** | 💰 Economic | 120 | Fast, budget-friendly |
| **Bytedance v1** | 💰 Economic | 150 | Social media (default) |
| **Hailuo I2V** | 💰 Economic | 180 | Artistic styles |
| **Runway Gen-3** | ⚡ High | 200 | Realistic content |
| **Kling v2.1 Pro** | ⚡ High | 250 | Anime & stylized |
| **Google Veo 3.1** | 👑 Premium | 350 | Maximum quality |
| **OpenAI Sora 2** | 👑 Premium | 400 | Complex narratives |

---

## 📐 Supported Formats

| Format | Dimensions | Use Case |
|--------|------------|----------|
| **9:16** (default) | 720 × 1280 | TikTok, Reels, Shorts |
| 16:9 | 1280 × 720 | YouTube horizontal |
| 1:1 | 720 × 720 | Instagram feed |

---

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

### Video Models
```http
GET /api/video-models
GET /api/recommended-model/{style_key}
GET /api/style-model-mapping
```

### Job Management
```http
POST /api/quick-create-full-universe
GET /api/status?job_id={job_id}
GET /api/jobs-hub
DELETE /api/jobs/{job_id}
```

### Styles
```http
GET /styles
```

---

## 📦 Project Structure

```
gen-scene-studio-backend/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── worker/
│   │   └── enterprise_manager.py  # Job processing & video models
│   ├── core/
│   │   ├── config.py           # Environment configuration
│   │   ├── db.py               # Database connection
│   │   └── logging.py          # Structured logging
│   ├── models/
│   │   ├── dao.py              # Data Access Objects
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   └── kie_client.py       # Kie.ai integration
│   └── utils/
│       ├── ffmpeg_cmds.py      # FFmpeg utilities
│       └── styles.py           # Style definitions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .github/workflows/          # CI/CD
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## ⚙️ Environment Variables

```env
# API Security
BACKEND_API_KEY=your_secure_api_key_here

# Database
DATABASE_URL=sqlite:///./data/genscene.db

# Media Storage
MEDIA_DIR=/app/media

# Worker Configuration
WORKER_CONCURRENCY=4
WORKER_POLL_INTERVAL=2

# Kie.ai Integration
KIE_API_KEY=your_kie_api_key
KIE_BASE_URL=https://api.kie.ai

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_enterprise_manager.py
```

---

## 🐳 Docker Deployment

### Build & Run

```bash
docker compose up -d --build
```

### View Logs

```bash
docker logs genscene-backend -f
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 📊 API Usage Example

### Create a Video

```bash
curl -X POST "https://api.genscenestudio.com/api/quick-create-full-universe" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "idea_text": "A dragon flying over a medieval castle at sunset",
    "duration": "30s",
    "style_key": "cinematic_realism",
    "auto_create_universe": true
  }'
```

### Response

```json
{
  "job_id": "qcf-abc12345",
  "episode_id": "ep-def67890",
  "status": "queued",
  "estimated_time_sec": 90,
  "message": "Full universe creation queued. Model: bytedance/v1-pro-text-to-video"
}
```

### Check Job Status

```bash
curl "https://api.genscenestudio.com/api/status?job_id=qcf-abc12345" \
  -H "X-API-Key: your_api_key"
```

---

## 🛡️ Security

- API Key authentication on all protected endpoints
- Rate limiting (60 requests/minute)
- CORS configured for allowed origins
- Input validation with Pydantic

---

## 📈 Performance

- Async I/O with asyncio
- Concurrent worker pool (configurable)
- Connection pooling for database
- Efficient video encoding with FFmpeg

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 👨‍💻 Author

**JuanFer85**

- GitHub: [@Juanfer85](https://github.com/Juanfer85)

---

<p align="center">
  <strong>🎬 Create. Generate. Dominate.</strong>
</p>

<p align="center">
  Made with ❤️ and AI
</p>
