# Medtrax HMS - Hospital Management System

Medtrax is a modern, feature-rich Hospital Management System (HMS) built with Django and Django Channels and containerized with Docker.

## Features

- **Authentication & Authorization**: Secure signup, login, and password reset functionalities with OTP verification via email.
- **Doctor & Patient Portals**: Separate dashboards and profiles for doctors and patients.
- **Appointments Management**: Book, schedule, and manage appointments.
- **Real-Time Chat & Video**: Integrated real-time chat rooms and video counseling using WebSockets (Django Channels) and Redis.
- **Prescription System**: Manage patient prescriptions.
- **Community Forum**: Participate in community discussions.
- **Asynchronous Tasks**: Background task execution using Celery and Redis.

## Tech Stack

- **Backend**: Python 3.12, Django 5.2.x, Django Rest Framework (DRF)
- **Real-Time**: Django Channels, Redis
- **Database**: PostgreSQL
- **Task Queue**: Celery, Redis
- **Containerization**: Docker, Docker Compose

## Folder Structure

The project has been organized to keep the root directory clean by moving all Django applications into the `apps/` directory. 

```
medtrax_hms/
├── apps/                   # Contains all Django applications
│   ├── Authapi/            # Authentication & Profiles
│   ├── appointments/       # Appointment Management
│   ├── chat_room/          # Real-Time WebSocket Chat
│   ├── community/          # Community Forums
│   ├── doctor_dashboard/   # Doctor's specific views
│   ├── patient_dashboard/  # Patient's specific views
│   ├── prescription/       # Prescriptions Management
│   └── videocounselling/   # Video Call Logic
├── medtrax/                # Main Django configuration (settings, urls, asgi, wsgi)
├── deploy/                 # Deployment and infrastructure configs
│   ├── docker/             # Docker configuration (Dockerfile, compose, env)
│   └── github/             # GitHub workflow templates
├── .env                    # Environment variables (Create this based on deploy/docker/.env.docker)
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

---

## Technical Appendix: Markdown vs. Markup

### Markup Language
A **Markup Language** is a system for annotating a document in a way that is syntactically distinguishable from the text. It uses **tags** to define elements, structure, and presentation.
*   **Example (HTML):**
    ```html
    <h1>Hospital Dashboard</h1>
    <p>Welcome to <strong>Medtrax</strong> HMS.</p>
    ```

### Markdown Language
A **Markdown Language** is a lightweight markup language with plain-text formatting syntax. It is designed to be highly readable for humans in its raw form and easily converted to HTML.
*   **Example (Markdown):**
    ```markdown
    # Hospital Dashboard
    Welcome to **Medtrax** HMS.
    ```

### Key Differences
| Feature | Markup (e.g., HTML) | Markdown |
| :--- | :--- | :--- |
| **Readability** | Lower (cluttered with tags) | Higher (looks like plain text) |
| **Complexity** | High (can define deep structures) | Low (focused on formatting) |
| **Syntax** | Uses `<tags>` | Uses `symbols` (e.g., `#`, `**`) |
| **Use Case** | Web development, data storage | Documentation, blogging, READMEs |


## Running Locally

The easiest way to run the project locally is using Docker Compose.

### Prerequisites
- Docker and Docker Compose installed.

### Steps

1. **Clone the repository.**
2. **Environment Variables**: Create a `.env` file in the root directory. You can copy `.env.docker` and customize it.
   ```bash
   cp .env.docker .env
   ```
3. **Start the containers**:
   ```bash
   docker-compose up --build
   ```
   This will start:
   - PostgreSQL Database (`db`)
   - Redis (`redis`)
   - Django Web Server (`web`) at `http://127.0.0.1:8000`
   - Celery Worker (`celery`)
   - Celery Beat (`celery-beat`)

4. **Access the application**:
   - The API will be available at `http://localhost:8000/api/`
   - The Admin panel will be available at `http://localhost:8000/admin/`

## Notes on Architecture

- **WebSockets**: We use Daphne as the ASGI server. Daphne properly handles both HTTP requests and WebSocket connections required for the `chat_room` and `videocounselling` apps.
- **Static & Media Files**: WhiteNoise handles static files serving. Ensure `DEBUG=False` in production for proper serving. Media files in production should ideally be stored in S3 or a similar block storage service.
