# Application Tracker Backend (apptrack-backend)

A secure, multi-user API for tracking job and scholarship applications with file attachments and reminders.

## Features

- User authentication with JWT (email/password)
- CRUD operations for applications
- File attachments with S3-compatible storage
- Application status tracking with history
- Email reminders via Celery
- RESTful API with detailed documentation

## Tech Stack

- Python 3.11
- Django 5.x
- Django REST Framework
- PostgreSQL 14+
- Redis
- Celery
- AWS S3/MinIO for file storage

## Local Development

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values
3. Run the services:

```bash
docker-compose up -d
```

4. Run migrations:

```bash
docker-compose exec web python manage.py migrate
```

5. Create a superuser:

```bash
docker-compose exec web python manage.py createsuperuser
```

6. Access the admin interface at: http://localhost:8000/admin/

### Running Tests

```bash
docker-compose exec web pytest
```

## API Documentation

See [API.md](API.md) for detailed API documentation with example requests and responses.

## Deployment

1. Set up a PostgreSQL database
2. Configure environment variables in production
3. Run migrations
4. Set up a production WSGI server (Gunicorn/Uvicorn)
5. Configure a reverse proxy (Nginx/Apache)
6. Set up SSL/TLS

## Environment Variables

See [.env.example](.env.example) for all required environment variables.

## License

MIT
