# Role-Based Access Control (RBAC) Full-Stack Application

This project is a complete full-stack web application implementing secure Authentication and Role-Based Access Control (RBAC). It fulfills the requirements for the Backend Developer (Intern) Assignment.

## Technology Stack

- **Backend:** Python, Flask, Flask-CORS, PyJWT, Bcrypt, SQLite
- **Frontend:** Vanilla HTML/JS, Tailwind CSS (via CDN)

> Note: Due to Node.js/npm not being available in the testing environment, the backend was built with Python (Flask) and a zero-config SQLite database. The frontend is built natively without a build step (Vanilla JS + Tailwind via CDN) so it can be run instantly by opening the HTML files.

## Setup Instructions

### 1. Backend Setup

The backend relies on Python 3.

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Activate the virtual environment (if it exists, or create a new one):
   ```bash
   # Create a virtual environment
   py -m venv venv
   
   # Activate it (Windows)
   .\venv\Scripts\activate
   
   # Or activate it (macOS/Linux)
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install flask flask-cors pyjwt bcrypt
   ```
4. Run the server:
   ```bash
   python app.py
   ```
   The backend will start on `http://localhost:5000` and automatically create the SQLite database `rbac_app.db`.

### 2. Frontend Setup

Since the frontend is built using standard web technologies, there's no build step required.
1. Simply open `frontend/index.html` in any web browser.
2. It will automatically redirect to the Login page.

## API Documentation

- **POST `/api/auth/register`**
  - **Description:** Register a new user.
  - **Body:** `{ "name": "...", "email": "...", "password": "...", "role": "User" | "Admin" }`
  - **Response:** `201 Created` on success, `409 Conflict` if email exists.

- **POST `/api/auth/login`**
  - **Description:** Authenticate and retrieve JWT.
  - **Body:** `{ "email": "...", "password": "..." }`
  - **Response:** `200 OK` with JWT token and user info.

- **GET `/api/users/me`**
  - **Description:** Retrieve current authenticated user profile.
  - **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  - **Response:** `200 OK` with user details.

- **GET `/api/users`**
  - **Description:** Retrieve all users (Admin ONLY).
  - **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  - **Response:** `200 OK` with list of all users, or `403 Forbidden` if not an admin.

## Scalability Note

Currently, the application uses **SQLite** for zero-configuration local testing and simplicity. To scale this backend system for a high-traffic production environment, the following architectural changes should be implemented:

1. **Database Migration:** Replace SQLite with a robust relational database like **PostgreSQL** or a NoSQL database like **MongoDB**. These databases are designed for high concurrency, clustering, and replication.
2. **Stateless Authentication:** The JWT approach implemented is already stateless, which allows the application servers to scale horizontally. The backend can be deployed across multiple instances behind a load balancer without needing to share session states.
3. **Caching Layer:** Introduce **Redis** to cache frequently accessed data (like user roles or the `/api/users` admin list) to reduce database load.
4. **Environment Variables:** Move the JWT secret and database credentials into secure environment variables and a secrets manager.
5. **Connection Pooling:** Use connection pooling for the database to efficiently manage and reuse database connections across multiple concurrent requests.
