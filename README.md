# AI Inventory Copilot

AI Inventory Copilot is a manufacturing inventory monitoring application that identifies stockout risk, prioritizes replenishment actions, and explains recommendations with a local AI assistant.

The project combines a deterministic risk engine with FastAPI, React, Docker, Excel reporting, automated tests, GitHub Actions, and Ollama.

## Features

- Inventory dashboard with operational KPIs
- Stockout risk score from 0 to 100
- Critical, high, medium, and low risk classification
- Days-of-cover calculation
- Reorder point calculation
- Supplier reliability factor
- Recommended replenishment quantity
- Search and risk-level filtering
- Excel risk report export
- Local AI inventory assistant with Ollama
- Deterministic fallback when the AI model is unavailable
- FastAPI REST API
- React dashboard
- Docker Compose environment
- Backend unit and API tests
- GitHub Actions continuous integration

## Risk model

The risk engine is intentionally deterministic. AI does not decide the risk score.

The score combines three operational signals:

1. Stock coverage compared with supplier lead time
2. Current stock position compared with the reorder point
3. Supplier delivery reliability

The reorder point is calculated as:

```text
reorder point = daily demand × lead time + safety stock
```

The engine then produces:

- risk score
- risk level
- days of cover
- projected shortage
- recommended order quantity
- human-readable reasons

This separation keeps the inventory decision logic testable and explainable. The AI layer is used to communicate the result and support operational questions.

## Architecture

```text
ai-inventory-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── services/
│   │       ├── copilot.py
│   │       ├── data_generator.py
│   │       └── risk_engine.py
│   ├── tests/
│   │   ├── test_api.py
│   │   └── test_risk_engine.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── .github/workflows/ci.yml
├── .env.example
├── docker-compose.yml
└── README.md
```

## Technology stack

### Backend

- Python
- FastAPI
- Pydantic
- HTTPX
- OpenPyXL
- Pytest

### Frontend

- React
- Vite
- Lucide React

### AI

- Ollama
- Llama 3.2 by default

### Infrastructure

- Docker
- Docker Compose
- GitHub Actions

## Run with Docker

Copy the environment example if you want to customize the configuration:

```bash
cp .env.example .env
```

Start the application:

```bash
docker compose up --build
```

The services will be available at:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
Ollama:   http://localhost:11434
```

Pull the default Ollama model after the containers are running:

```bash
docker compose exec ollama ollama pull llama3.2:3b
```

The application remains usable if Ollama is not ready. In that case, the copilot returns a deterministic explanation generated from the risk-engine results.

## Run locally without Docker

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows:

```bash
.venv\Scripts\activate
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The development frontend will be available at `http://localhost:5173`.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health check |
| GET | `/products` | List inventory items |
| GET | `/products/{sku}/risk` | Get one SKU risk assessment |
| GET | `/risks` | List all risk assessments ordered by score |
| GET | `/dashboard` | Get dashboard KPIs |
| POST | `/copilot` | Ask the inventory copilot a question |
| GET | `/export` | Download the Excel inventory risk report |

### Copilot request example

```json
{
  "question": "What should I prioritize for this item?",
  "sku": "MAT-0001"
}
```

## Tests

Run the backend test suite from the `backend` directory:

```bash
pytest -q
```

The current tests cover:

- healthy stock conditions
- critical stock conditions
- reorder-point calculation
- days-of-cover calculation
- score boundaries
- API health
- inventory retrieval
- dashboard summary
- unknown SKU handling
- Excel export

## Continuous integration

The GitHub Actions workflow runs on pushes and pull requests to `main`.

It performs two independent checks:

- Python dependency installation and backend tests
- Node dependency installation and production frontend build

## Demo data

The application generates 40 deterministic manufacturing inventory records. A fixed random seed keeps the dataset stable between runs so risk calculations and tests remain reproducible.

The sample data includes:

- raw materials
- fasteners
- electrical components
- packaging
- machined parts
- supplier lead times
- supplier reliability
- safety stock
- unit costs
- daily demand

## Design decisions

The AI assistant is deliberately separated from the risk calculation. Inventory risk is calculated with explicit business rules, which makes the result auditable and testable. Ollama receives the calculated context and explains it in operational language rather than inventing the underlying recommendation.

The demo dataset is generated in memory to keep the repository easy to run. A production version could replace it with PostgreSQL or ERP data without changing the risk-engine interface.

## Possible next steps

- PostgreSQL persistence
- ERP or purchasing-system integration
- historical consumption ingestion
- demand forecasting
- supplier performance history
- authentication and role-based access
- configurable risk weights
- purchase-order workflow
- alerting for newly critical items
- deployment to a cloud environment
