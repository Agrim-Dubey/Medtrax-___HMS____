# Medtrax HMS - Hospital Management System (Backend)

Medtrax is a production-ready Hospital Management System (HMS) built with Django, Django Channels, PostgreSQL, Redis, Celery, and containerized with Docker.

---

## Features

- **Authentication & Authorization**: Custom user model with dual profiles (Doctor & Patient), JWT auth via HTTP-only cookies, and email OTP verification.
- **Appointments Management**: Dynamic slot generation, appointment booking, acceptance/rejection workflows, and real-time waiting queue calculations.
- **Real-Time Chat & Video**: WebSocket chat rooms and WebRTC video signaling powered by Django Channels and Redis.
- **Doctor & Patient Dashboards**: Statistics, upcoming/past schedules, weekly agendas, and patient review management.
- **Prescription System**: Structured medical prescriptions with nested medication tracking and diagnostic test orders.
- **Community Forum**: Category-based health discussions with nested replies, comments, and like reactions.
- **Asynchronous Tasks**: Background task execution and scheduled jobs managed by Celery and Redis.

---

## Tech Stack

- **Framework**: Python 3.12, Django 5.2.x, Django Rest Framework (DRF)
- **ASGI & WebSockets**: Daphne, Channels, Channels-Redis
- **Database**: PostgreSQL (with connection pooling via `dj-database-url`)
- **Cache & Message Broker**: Redis
- **Task Queue & Scheduler**: Celery, django-celery-beat, django-celery-results
- **Containerization & CI/CD**: Docker, Docker Compose, GitHub Actions

---

## Folder Structure

The backend follows a modular domain-driven architecture, organizing all business domains into `apps/`:

```text
medtrax-backend/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions Docker build & EC2 deploy
├── apps/                       # Modular Django applications
│   ├── Authapi/                # User authentication, OTP, JWT, & profile models
│   ├── appointments/           # Appointment slots, booking, & queue WebSockets
│   ├── chat_room/              # Direct chat rooms, messaging, & networking
│   ├── community/              # Health forums, posts, comments, & reactions
│   ├── doctor_dashboard/       # Doctor analytics, schedules, & reviews
│   ├── patient_dashboard/      # Patient portal, statistics, & appointments
│   ├── prescription/           # Medical prescriptions & medications
│   └── videocounselling/       # Video consultations & WebRTC signaling
├── config/                     # Django project core (modular settings, URLs, ASGI/WSGI, Celery)
│   ├── settings/               # Environment-split settings (base, development, production)
├── static/                     # Source vendor static assets (AdminLTE, Select2, Jazzmin)
├── templates/                  # Global templates directory
├── Dockerfile                  # Production multi-stage Docker build
├── compose.yml                 # Local container orchestration (web, db, redis, celery, prometheus, grafana, alertmanager)
├── .env.example                # Documented environment variables template
├── manage.py                   # Django management CLI
└── requirements.txt            # Python dependencies
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- Alternatively, Python 3.12+ and PostgreSQL + Redis locally.

### 1. Environment Configuration

Copy the example environment file and adjust credentials as needed:

```bash
cp .env.example .env
```

### 2. Run with Docker Compose

Build and launch the complete stack:

```bash
docker compose up --build
```

This launches:
- **`web`**: Daphne ASGI server on `http://127.0.0.1:8000`
- **`db`**: PostgreSQL 15 on port `5432`
- **`redis`**: Redis 7 on port `6379`
- **`celery`**: Celery worker for async background jobs
- **`celery-beat`**: Celery periodic task scheduler

### 3. Verification & Access

- **API Root**: `http://localhost:8000/api/`
- **Swagger Docs**: `http://localhost:8000/swagger/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## Architecture Details

- **WebSockets & Real-Time**: Daphne is configured in `config.asgi` to route both HTTP requests and WebSocket connections (`/ws/chat/`, `/ws/video/`, `/ws/queue/`).
- **Stateless Authentication**: JWT tokens are issued on login and stored in secure, `SameSite=None` HTTP-only cookies with rotating refresh tokens.
- **Static Assets**: WhiteNoise (`CompressedManifestStaticFilesStorage`) manages asset serving in containerized deployments.
