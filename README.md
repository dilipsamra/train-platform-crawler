# Train Platform Crawler

This project is a modular web application for scanning UK National Rail arrivals and departures from a given station. It is structured for easy extension (e.g., notifications, disruption alerts, mobile support).

## Structure
- `backend/` — FastAPI Python backend (API, National Rail integration)
- `frontend/` — React TypeScript frontend (UI)

## Quick Start

### Backend
1. `cd backend`
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Create a `.env` file with your National Rail Darwin API token:
   ```
   DARWIN_TOKEN=your_token_here
   ```
5. `uvicorn main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm start`

## Docker Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### Build and Run (Backend + Frontend)

1. Copy your `.env` file into `backend/.env` (for Darwin token, etc).
2. From the project root, run:
   ```sh
   docker-compose up --build
   ```
3. Access the apps:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000

### Stopping
To stop the containers:
```sh
docker-compose down
```

### Development
- Code changes in `backend/` and `frontend/` will auto-reload in Docker containers.
- For production, you may want to adjust Dockerfiles for optimized builds.

## Features
- Input a station (e.g., London Euston)
- See last 5 and next 5 arrivals/departures, platform, operator
- Modular for future features (notifications, disruption alerts, mobile)
