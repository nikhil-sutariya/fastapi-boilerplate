# FastAPI with PostgreSQL

A production-ready FastAPI application with PostgreSQL database, SQLAlchemy ORM, and comprehensive authentication system.

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Migrations](#database-migrations)
- [Docker Deployment](#docker-deployment)
- [Development Guidelines](#development-guidelines)

## ✨ Features

- **FastAPI Framework** - Modern, fast web framework for building APIs
- **PostgreSQL Database** - Robust, ACID-compliant relational database
- **SQLAlchemy ORM** - Async SQLAlchemy with proper connection pooling
- **Authentication System** - JWT-based authentication with refresh tokens
- **User Management** - Registration, login, profile management, password reset
- **Real-time Notifications** - WebSocket-based notification system
- **Audit Logging** - Comprehensive logging system for all user actions
- **Email Integration** - SMTP email service for notifications and password reset
- **File Upload** - Profile picture upload with validation
- **Database Migrations** - Alembic for schema versioning and migrations
- **Production Ready** - Proper error handling, logging, and security

## 🔧 Requirements

- **Python 3.10+**
- **PostgreSQL 12+**
- **Docker** (optional, for containerized deployment)

## 📁 Project Structure

```
fastapi-boilerplate/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── deps/                   # Dependencies
│   │   │   ├── __init__.py
│   │   │   └── auth_deps.py        # Authentication dependencies
│   │   └── routes/                 # API routes
│   │       ├── __init__.py
│   │       ├── auth.py             # Authentication routes
│   │       └── logging.py          # Logging routes
│   ├── core/                       # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration settings
│   │   ├── constants.py            # Application constants
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── logging.py              # Logging configuration
│   │   ├── permission.py           # Permission system
│   │   ├── response.py             # Response utilities
│   │   ├── security.py             # Security utilities (JWT, password hashing)
│   │   └── socket_manager.py       # WebSocket manager
│   ├── db/                         # Database layer
│   │   ├── __init__.py
│   │   └── database.py             # Database connection and session management
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py                 # User, Notification, Log models
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py      # Base repository with CRUD operations
│   │   ├── logging.py              # Logging repository
│   │   └── user_repository.py      # User repository
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── logging.py              # Logging schemas
│   │   └── user.py                 # User schemas
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   └── user_service.py         # User service
│   ├── messages/                   # Message constants
│   │   ├── __init__.py
│   │   ├── logging.py              # Logging messages
│   │   └── user.py                 # User messages
│   ├── middleware/                 # Custom middleware
│   │   ├── __init__.py
│   │   └── error_logging.py        # Error logging middleware
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── date_formatting.py      # Date formatting utilities
│   │   └── send_email.py           # Email sending utilities
│   ├── templates/                  # Email templates
│   │   └── forgot_password.html    # Password reset email template
│   └── tests/                      # Test files
│       ├── __init__.py
│       ├── integration/            # Integration tests
│       │   └── test_auth_route.py
│       └── unit/                   # Unit tests
│           └── test_auth_service.py
├── alembic/                        # Database migrations
│   ├── versions/                   # Migration files
│   ├── env.py                      # Alembic environment configuration
│   └── script.py.mako              # Migration template
├── uploads/                        # File uploads directory
│   └── profile_pictures/           # User profile pictures
├── alembic.ini                     # Alembic configuration
├── Dockerfile                      # Docker configuration
├── requirements.txt                # Python dependencies
├── requirements-core.txt           # Core dependencies
└── README.md                       # This file
```

## 🔐 Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
# Application Configuration
APP_TITLE=Fastapi Boilerplate
APP_VERSION=1.0.0
ENVIRONMENT=development

# Database Configuration (PostgreSQL)
DB_HOSTNAME=localhost
DB_PORT=5432
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

# Security Configuration
SECRET_KEY=your-secret-key-here-make-it-long-and-random
OAUTH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Client Origins (CORS) - Comma-separated list
CLIENT_ORIGINS=http://localhost:3000,http://localhost:8080

# Frontend URLs
FRONTEND_HOST_URL=http://localhost:3000
FRONTEND_FORGET_PASSWORD_URL=reset-password
FRONTEND_SIGNUP_URL=signup

# Email Configuration (SMTP)
SMTP_EMAIL_FROM=noreply@yourdomain.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fastapi-boilerplate
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 🗄️ Database Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [PostgreSQL Official Website](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE your_db_name;
CREATE USER your_db_username WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_username;
\q
```

## 🏃‍♂️ Running the Application

### Development Mode

```bash
# Start the development server
fastapi dev

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Start the production server
fastapi run

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/logout` | User logout |
| POST | `/api/v1/auth/refresh-token` | Refresh access token |
| POST | `/api/v1/auth/forget-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |
| PATCH | `/api/v1/auth/change-password` | Change password (authenticated) |
| GET | `/api/v1/auth/get-profile` | Get user profile |
| PATCH | `/api/v1/auth/update-profile/{user_id}` | Update user profile |
| PATCH | `/api/v1/auth/upload-profile-picture/{user_id}` | Upload profile picture |
| GET | `/api/v1/auth/get-notifications` | Get user notifications |
| PUT | `/api/v1/auth/notification-seen` | Mark notifications as seen |
| GET | `/api/v1/auth/ws-token` | Get WebSocket token |
| WebSocket | `/api/v1/auth/ws/notifications` | Real-time notifications |

### Logging Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/logs/get-logs` | Get user activity logs |

## 🔄 Database Migrations

This project uses Alembic for database schema management.

### Initialize Alembic (First Time Only)

```bash
# Initialize Alembic in your project
alembic init alembic
```

### Create a New Migration

```bash
# Create a new migration file
alembic revision --autogenerate -m "Description of changes"

# Or create an empty migration file
alembic revision -m "Description of changes"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Apply next migration only
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback to previous migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Migration Status

```bash
# Check current migration status
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

### Example Migration Workflow

```bash
# 1. Make changes to your SQLAlchemy models
# 2. Create migration
alembic revision --autogenerate -m "Add user preferences table"

# 3. Review the generated migration file in alembic/versions/
# 4. Apply the migration
alembic upgrade head

# 5. Verify changes in database
```

## 🐳 Docker Deployment

### Build Docker Image

```bash
# Build the Docker image
docker build -t fastapi-boilerplate-api:latest .
```

### Run with Docker

```bash
# Run the container
docker run -p 8000:8000 \
  --name fastapi-boilerplate \
  --rm \
  -e DB_HOSTNAME=host.docker.internal \
  -e DB_USERNAME=your_username \
  -e DB_PASSWORD=your_password \
  -e DB_NAME=your_database \
  fastapi-boilerplate-api:latest
```

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOSTNAME=postgres
      - DB_USERNAME=postgres
      - DB_PASSWORD=password
      - DB_NAME=your_db_name
      - SECRET_KEY=your-secret-key
    depends_on:
      - postgres
    volumes:
      - ./uploads:/app/uploads

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=your_db_name
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Run with Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Development Guidelines

### Code Structure

1. **Models** (`app/models/`) - SQLAlchemy database models
2. **Schemas** (`app/schemas/`) - Pydantic models for API validation
3. **Repositories** (`app/repositories/`) - Data access layer
4. **Services** (`app/services/`) - Business logic layer
5. **Routes** (`app/api/routes/`) - API endpoints
6. **Dependencies** (`app/api/deps/`) - Shared dependencies

### Adding New Features

1. **Create SQLAlchemy Model** in `app/models/`
2. **Create Pydantic Schemas** in `app/schemas/`
3. **Create Repository** in `app/repositories/`
4. **Create Service** in `app/services/`
5. **Create Routes** in `app/api/routes/`
6. **Create Migration** with `alembic revision --autogenerate`

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_auth_service.py
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `APP_TITLE` | Application title | Yes | - |
| `APP_VERSION` | Application version | Yes | - |
| `ENVIRONMENT` | Environment (development/production) | Yes | - |
| `DB_HOSTNAME` | Database host | Yes | - |
| `DB_PORT` | Database port | Yes | - |
| `DB_USERNAME` | Database username | Yes | - |
| `DB_PASSWORD` | Database password | Yes | - |
| `DB_NAME` | Database name | Yes | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `OAUTH_ALGORITHM` | JWT algorithm | No | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | No | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | No | 7 |

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify database credentials
   - Ensure database exists

2. **Migration Errors**
   - Check for syntax errors in migration files
   - Ensure database is up to date
   - Review migration history

3. **Authentication Issues**
   - Verify JWT secret key is set
   - Check token expiry settings
   - Ensure proper CORS configuration

### Logs

Check application logs for detailed error information:

```bash
# View logs in development
tail -f logs/app.log

# View Docker logs
docker logs fastapi-boilerplate
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions, please open an issue in the repository.
