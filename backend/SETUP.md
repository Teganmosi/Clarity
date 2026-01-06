# Backend Setup Guide

This guide will help you set up and run the Lead Scoring Engine backend.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation Steps

### 1. Navigate to the Backend Directory

```bash
cd lead-scoring-engine/backend
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
```

**Mac/Linux:**

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Mac/Linux:**

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-api-key-here-change-in-production

# Database
DATABASE_URL=sqlite:///./leads.db

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=alerts@yourcompany.com

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Lead Scoring
SCORE_THRESHOLD_HIGH=80
SCORE_THRESHOLD_MEDIUM=50

# CRM Integrations (Optional)
HUBSPOT_API_KEY=your-hubspot-api-key
PIPEDRIVE_API_KEY=your-pipedrive-api-key
```

### 6. Run the Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database

The application uses SQLite by default. The database file (`leads.db`) will be created automatically in the backend directory on first run.

### Resetting the Database

To reset the database, simply delete the `leads.db` file and restart the server:

```bash
rm leads.db  # Mac/Linux
del leads.db  # Windows
```

## Testing the API

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testuser"
```

### Create a Lead

```bash
curl -X POST "http://localhost:8000/leads/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp",
    "source": "website",
    "past_interactions": 5
  }'
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, you can change the port in the `.env` file or run:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Import Errors

If you encounter import errors, make sure you've installed all dependencies:

```bash
pip install -r requirements.txt
```

### CORS Errors

If you encounter CORS errors when connecting from the frontend, check the `CORS_ORIGINS` in your `.env` file includes your frontend URL.

## Production Deployment

For production deployment:

1. Use a production-grade database (PostgreSQL, MySQL)
2. Set strong API keys and secrets
3. Use a production WSGI server (Gunicorn, uWSGI)
4. Enable HTTPS
5. Set up proper logging and monitoring

Example production command:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
