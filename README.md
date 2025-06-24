# Train Platform Crawler

This project is a modular web application for viewing UK National Rail arrivals and departures from a given station, using the Rail Data Marketplace Live Departure Board REST API.

## Structure

- `backend/` — FastAPI Python backend (API, National Rail integration)
- `frontend/` — React TypeScript frontend (UI)

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Rail Data Marketplace account with access to the Live Departure Board API

### Setup

#### 1. Get Your API Key

- Subscribe to the "Live Departure Board" product on Rail Data Marketplace.
- Copy your API key (consumer key) from the portal.

#### 2. Configure Environment Variables

- In the project root, copy your API key into `backend/.env`:

  ```env
  CONSUMER_KEY=your_actual_api_key
  LDBWS_BASE_URL=https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120
  ```

#### 3. Build and Run with Docker

From the project root, run:

```sh
docker compose up --build
```

- Backend API: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:3000](http://localhost:3000)

#### 4. Stopping

To stop the containers:

```sh
docker compose down
```

## API Usage

- Arrivals: `GET /station/{crs_code}/arrivals`
- Departures: `GET /station/{crs_code}/departures`
- Example: [http://localhost:8000/station/KGX/departures](http://localhost:8000/station/KGX/departures)

You can import the OpenAPI spec from [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) into Postman for easy testing.

## Development

- Code changes in `backend/` and `frontend/` will auto-reload in Docker containers.
- For production, you may want to adjust Dockerfiles for optimized builds.

## Features

- Input a station (e.g., London Euston)
- See last 5 and next 5 arrivals/departures, platform, operator
- Modular for future features (notifications, disruption alerts, mobile)
