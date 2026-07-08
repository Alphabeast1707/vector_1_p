# EnFormis Vector 1 - Bayesian Active Learning Engine

Welcome to the **EnFormis Vector 1 (Module 3)** codebase. This repository contains the high-performance manufacturing intelligence engine for active design of experiments (DoE) and process optimization, using advanced Bayesian optimization via BoTorch/PyTorch with a dynamic React-based Active Learning Dashboard.

---

## 📌 Core Features

- **Bayesian Active Learning Core**: Implements a robust multi-objective Bayesian optimization active loop utilizing Gaussian Processes (GP) with Matérn kernels.
- **Advanced Acquisition Functions**: Uses `qLogNoisyExpectedHypervolumeImprovement` (qLogNEHVI) for reliable hypervolume improvement suggestion even in noisy physical formulation spaces.
- **Physical & Formulation Constraints**: Full support for mass-balance formulation constraints (e.g. excipients sum <= 70%), physical boundary limits, and thermal/glass transition parameters.
- **High-Dimensional Scaling Optimization**: Includes intelligent historical baseline point pruning (down to $N \le 4$) in 8D spaces to prevent CPU hypervolume partitioning from running into exponential box-decomposition bottlenecks and freezing.
- **FastAPI Backend Core**: Highly-scalable async backend endpoints for initializing domains, adding lab experimental results, and generating optimal suggestions.
- **Interactive React Dashboard**: Live visualization dashboard allowing scientists to configure limits, visualize optimization progress, submit manual lab results, and receive BoTorch suggestions.

---

## 📁 Repository Structure

```text
├── .gitignore                      # Workspace ignores (environments, cash, OS files)
├── backend/
│   ├── .gitignore                  # Virtual environment ignores
│   ├── main.py                     # FastAPI application setup and CORS configuration
│   ├── requirements.txt            # Python dependencies (botorch, fastapi, uvicorn, etc.)
│   ├── engines/
│   │   ├── domain_builder.py       # Domain construction from profile and strategy cards
│   │   ├── gp_model.py            # Gaussian Process model setup
│   │   ├── acquisition.py         # qLogNEHVI acquisition function with pruning logic
│   │   └── bo_loop.py             # Active learning state loop (LHS seed -> GP fit -> Optimize)
│   ├── routers/
│   │   └── v1_bayesian_doe.py     # FastAPI HTTP route handlers (/domain, /experiments/result, /suggest)
│   ├── schemas/
│   │   └── shared_db_schemas.py   # Pydantic schemas (ProfileCard, StrategyCard, etc.)
│   └── tests/                      # Python pytest validation suites
│       ├── test_v1_bo.py           # Core bounds validation checks
│       ├── test_v1_bo_botorch.py   # active BoTorch simulation tests
│       ├── test_v1_phase1_integration.py # Phase 1 integration schema verification
│       └── test_v1_router.py       # API routing and handler verification
├── data/                           # Historical research datasets (Team Alpha, Team Beta, dummy, etc.)
│   ├── Final Dataset.json
│   ├── team alpha finalised dummy dataset.json
│   ├── team beta finalised dummy dataset.json
│   ├── team_alpha_dummy.csv
│   └── team_beta_dummy.csv
├── frontend/
│   └── src/
│       └── components/
│             └── Vector1/
│                   └── ActiveLearningDashboard.jsx  # React Dashboard component
└── phase1/
    └── phase1_output.json          # Pareto solution reference output required for integration tests
```

---

## 📊 Output Data & Datasets

This repository preserves all primary physical formulation output data and historical raw development datasets:

### 1. Phase 1 Optimization Output (`phase1/phase1_output.json`)
This is the core optimized data deliverable of the Phase 1 optimization sweep. It contains:
- **API Target**: `Paracetamol` (BCS Class I).
- **Primary Technique**: `wet_granulation` (Technique confidence: `0.699`).
- **Optimization Sweep Space**: Run across 23 physical experiments, mapping 17 critical process parameters (CPPs) and critical material attributes (CMAs).
- **Pareto Optimal Frontiers**: 16 distinct multi-objective Pareto-optimal solutions with optimized physical properties (CPP concentrations of Lactose Monohydrate, Starch 1500, DCPA, MCC PH101, PEG, HPC LF, Mannitol, drying temperatures, compression forces, scale parameters, and impeller/blade speeds).
- **Predicted CQAs**: Each Pareto-optimal solution includes mean, standard deviation, and 95% confidence intervals for physical manufacturing attributes:
  - *Hardness (N)*
  - *Dissolution (30min %)*
  - *Friability (%)*

*Note: This dataset is parsed programmatically inside `backend/tests/test_v1_phase1_integration.py` to ensure schema constraints, physical mass balance, and data fidelity of Phase 1 solutions.*

### 2. Historical & Dummy Production Datasets (`data/`)
The `data/` folder contains original experimental trials and complete final datasets used during model research:
- **`data/Final Dataset.json`**: An extensive formulation mapping database (176,780+ lines) detailing full process and recipe metrics.
- **`data/team alpha finalised dummy dataset.json`**: Historical development trial database for Team Alpha.
- **`data/team beta finalised dummy dataset.json`**: Historical development trial database for Team Beta.
- **`data/team_alpha_dummy.csv` & `data/team_beta_dummy.csv`**: Structured CSV equivalents of Team Alpha and Team Beta initial trial configurations.

---

## 🛠️ Installation & Setup

### 1. Backend Setup (FastAPI & BoTorch)

A virtual environment is already created at `backend/venv/`. To activate and start the service:

```bash
# Navigate to backend directory
cd backend/

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt
```

### 2. Frontend Setup (React)

The frontend is implemented as a React Component designed to run inside a Vite environment. Ensure your frontend proxy or environment is pointing to port `8001` where the backend runs, or configure the fetch endpoints in `ActiveLearningDashboard.jsx` as needed.

---

## 🚀 Running the Services

### 1. Start the FastAPI Backend
With your virtual environment active, run the Uvicorn server:
```bash
cd backend/
PYTHONPATH=. venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
The server will start up and run at `http://localhost:8001`. You can view the fully documented Swagger API interactive docs at `http://localhost:8001/docs`.

### 2. Integrate the React Dashboard
Import the `ActiveLearningDashboard` component in your React application routes or container:
```javascript
import ActiveLearningDashboard from './components/Vector1/ActiveLearningDashboard';
```

---

## 🧪 Running Tests

The workspace features a comprehensive validation test suite powered by `pytest`.

Ensure you are in the `backend/` directory, and execute the following:

```bash
# Run the entire test suite with PYTHONPATH configured
cd backend/
PYTHONPATH=. venv/bin/pytest tests/
```

### What gets verified:
- **`test_v1_bo.py`**: Standard physical bounds validation.
- **`test_v1_bo_botorch.py`**: Multi-round optimization loop. Seeds 3 initialization experiments with Latin Hypercube Sampling (LHS), submits mock physical values, builds GP models, and generates acquisition suggestions.
- **`test_v1_phase1_integration.py`**: Verifies processing and structure of the Phase 1 Pareto front schema.
- **`test_v1_router.py`**: Ensures all REST endpoints successfully serialize and validate schema inputs.
