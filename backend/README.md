# Health Tracker Backend

This directory contains the Python FastAPI backend for the Health Tracker application.

## Features

*   User authentication (signup, login) using JWT.
*   CRUD operations for health entries (text logging).
*   Integration with Google Gemini for parsing natural language health entries (food, weight, steps) and estimating nutritional info.
*   RESTful API endpoints.

## Technology Stack

*   Python 3.x
*   FastAPI: Web framework
*   SQLAlchemy: ORM for database interaction
*   Pydantic: Data validation
*   Uvicorn: ASGI server
*   SQLite: Database (for development)
*   Passlib[bcrypt]: Password hashing
*   python-jose[cryptography]: JWT handling
*   google-generativeai: Google Gemini API client
*   python-dotenv: Environment variable management

## Setup

1.  **Navigate to Backend Directory:**
    ```bash
    cd backend
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the `.env.example` file (if one exists) or create a new `.env` file in the `backend` directory.
    *   Update the following variables in `.env`:
        *   `DATABASE_URL`: Defines the database connection string. Defaults to SQLite (`sqlite:///./health_tracker.db`). The `./` means the file will be created in the directory where you run `uvicorn`.
        *   `SECRET_KEY`: A strong secret key for JWT signing. You can generate one using `openssl rand -hex 32`.
        *   `GOOGLE_API_KEY`: Your API key from Google AI Studio for using the Gemini model.

## Database

*   The application uses SQLAlchemy to interact with the database.
*   Currently, it uses SQLite, creating a `health_tracker.db` file.
*   Database tables are created automatically on startup via `Base.metadata.create_all(bind=engine)` in `main.py`. **Note:** This method does not handle migrations. If you change the models (e.g., add columns), you may need to delete the `health_tracker.db` file during development for the changes to apply.
*   For production or more complex development, using a migration tool like **Alembic** is highly recommended.

## Running the Application

1.  **Ensure you are in the `backend` directory** (or the project root, depending on where you want the `.db` file created relative to the `DATABASE_URL` setting).
2.  **Run the Uvicorn server:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `main:app`: Tells uvicorn to look for the file `main.py` in the current directory (`backend/`) and find the object named `app` inside it.
    *   `--reload`: Enables auto-reloading on code changes (useful for development).
    *   `--host 0.0.0.0`: Makes the server accessible on your network (use `127.0.0.1` for local access only).
    *   `--port 8000`: Specifies the port to run on.

3.  **Access the API Documentation:**
    Once the server is running, you can access the interactive API documentation (Swagger UI) at [http://localhost:8000/docs](http://localhost:8000/docs).

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py         # API dependencies (get_db, get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py        # Main v1 API router
│   │       └── endpoints/    # Specific endpoint modules (auth.py, entries.py)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration loading (from .env)
│   │   └── security.py     # Password hashing, JWT creation
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py         # Base CRUD class
│   │   ├── crud_user.py    # User specific CRUD
│   │   └── crud_health_entry.py # HealthEntry specific CRUD
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py         # Imports models, Base for metadata
│   │   ├── base_class.py   # Declarative Base definition
│   │   └── session.py      # Database engine and session setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py         # User model
│   │   └── health_entry.py # HealthEntry model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── token.py        # Token schemas
│   │   ├── user.py         # User schemas
│   │   └── health_entry.py # HealthEntry schemas
│   └── services/
│       ├── __init__.py
│       └── llm_parser.py   # Gemini LLM interaction logic
├── .env                # Environment variables (DATABASE_URL, SECRET_KEY, GOOGLE_API_KEY) - *DO NOT COMMIT* 
├── main.py             # Main FastAPI application entrypoint
├── requirements.txt    # Python dependencies
└── README.md           # This file
``` 