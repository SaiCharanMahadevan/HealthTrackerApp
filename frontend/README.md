# Health Tracker Frontend

This directory contains the React frontend for the Health Tracker application, built using Vite.

## Features

*   User interface for signup, login, and health data logging.
*   Displays logged health entries, including parsed data from the backend LLM.
*   Routing between different pages.
*   Basic JWT authentication handling (token storage, protected routes).

## Technology Stack

*   React.js
*   Vite: Build tool and development server
*   JavaScript (ES6+)
*   Axios: For making HTTP requests to the backend API
*   React Router DOM: For client-side routing
*   CSS (basic styling in `index.css` and `App.css`)

## Setup

1.  **Navigate to Frontend Directory:**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies:**
    Make sure you have Node.js and npm installed (using `nvm` is recommended for managing Node versions).
    ```bash
    npm install
    ```

3.  **Configure Environment Variables (Optional):**
    *   The frontend tries to connect to the backend API specified by `VITE_API_BASE_URL`.
    *   You can create a `.env.local` file in the `frontend` directory to override the default backend URL (`http://localhost:8000/api/v1`).
    *   Example `.env.local`:
        ```
        VITE_API_BASE_URL=http://your-backend-host:port/api/v1
        ```

## Running the Development Server

1.  **Ensure the backend server is running.** (See backend README).
2.  **Start the Vite development server:**
    ```bash
    npm run dev
    ```
3.  This will typically start the frontend application on [http://localhost:5173](http://localhost:5173) (Vite usually picks the next available port if 5173 is busy).

## Building for Production

To create an optimized build for deployment:

```bash
npm run build
```

This will generate static assets in the `frontend/dist` directory, which can then be served by a static file server.

## Project Structure

```
frontend/
├── public/             # Static assets (e.g., favicon)
├── src/
│   ├── assets/         # Static assets used in components (e.g., images, logos)
│   ├── components/     # Reusable UI components (currently empty)
│   ├── contexts/       # React context providers (currently empty)
│   ├── hooks/          # Custom React hooks (currently empty)
│   ├── pages/          # Page-level components (HomePage, LoginPage, SignupPage)
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   └── SignupPage.jsx
│   ├── services/       # API interaction logic
│   │   └── api.js        # Axios setup and API call functions
│   ├── App.css         # Main application styles
│   ├── App.jsx         # Root application component with routing setup
│   ├── index.css       # Global styles
│   └── main.jsx        # Application entry point (renders App)
├── .env.local        # Local environment variables (optional, *DO NOT COMMIT*)
├── .gitignore          # Git ignore rules
├── index.html          # Main HTML template
├── package.json        # Project metadata and dependencies
├── package-lock.json   # Locked dependency versions
├── README.md           # This file
└── vite.config.js      # Vite configuration
```
