# Train Platform Crawler Backend

This is the backend service for the Train Platform Crawler application. It uses FastAPI to provide RESTful APIs for fetching train arrivals and departures from UK National Rail stations.

## Structure
- `main.py`: FastAPI app entry point
- `services/`: Logic for interacting with National Rail APIs
- `models/`: Pydantic models for request/response
- `utils/`: Utility functions

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn httpx python-dotenv
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## Environment Variables
Create a `.env` file with your National Rail API credentials:
```
DARWIN_TOKEN=your_national_rail_darwin_token
```

## Endpoints
- `/station/{crs_code}/arrivals`
- `/station/{crs_code}/departures`

## API Documentation

FastAPI provides interactive API docs out of the box:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

You can use these to explore and test the API directly in your browser.

