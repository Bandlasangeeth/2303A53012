# Vehicle Maintenance Scheduler Microservice

This microservice provides dynamic optimization for scheduling vehicle maintenance tasks based on mechanic availability using the 0/1 Knapsack Algorithm.

## Setup
Ensure you provide the API token in a `.env` file at the root.

```env
ACCESS_TOKEN=your_token_here
```

## Running the application
To run the server locally:
```bash
pip install -r requirements.txt
uvicorn vehicle_scheduler_be.app.main:app --host 0.0.0.0 --port 8000
```

Alternatively, use Docker:
```bash
docker build -t vehicle-scheduler .
docker run -p 8000:8000 -e ACCESS_TOKEN=your_token vehicle-scheduler
```

## Endpoints

- `POST /scheduler/optimize`: Fetches depots and vehicles from the evaluation service, runs the Dynamic Programming optimization to maximize impact within available mechanic hours, and returns the selected tasks.
