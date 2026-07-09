# EnFormis Manufacturing Intelligence Core — Module 3 (Team Gamma)

Welcome to the **EnFormis Module 3 (Team Gamma)** production codebase. This repository contains high-performance manufacturing intelligence engines, mechanistic modeling platforms, and machine learning correctors for advanced active design of experiments (DoE) and process scale-up.

This repository features a **Multi-Vector Architecture** accessible through a unified dashboard interface:
- 🔬 **Vector 1 (Active Learning)**: Multi-objective Bayesian active experimentation engine using Gaussian Processes (GP) and `qLogNEHVI` acquisition routines.
- ⚙️ **Vector 2 (Scale-Up)**: Digital Twin physical simulator using Froude and Tip Speed dimensionless scaling coupled with a pre-trained ML residual corrector layer.
- 🛡️ **Vector 3 (Risk Audit)**: GMP compliance failure mode evaluator generating immutable `ProcessDevelopmentCard` files (Delta/Epsilon handoff).

---

## 📁 Repository Structure

```text
├── .gitignore                      # Workspace ignores (environments, cache, OS files)
├── README.md                       # Comprehensive system documentation
├── backend/
│   ├── .gitignore                  # Virtual environment and local package ignores
│   ├── main.py                     # Entry point for the FastAPI server & CORS middleware
│   ├── requirements.txt            # Python dependencies (botorch, fastapi, uvicorn, etc.)
│   ├── engines/
│   │   ├── data_ingestion.py       # Reads and cross-validates Team Alpha and Team Beta datasets
│   │   ├── domain_builder.py       # Dynamically constructs physics-informed design spaces from API data
│   │   ├── gp_model.py             # SingleTaskGP initialization with Matérn 5/2 covariance kernels
│   │   ├── acquisition.py          # Log-Noisy Expected Hypervolume Improvement (qLogNEHVI) logic
│   │   ├── bo_loop.py              # Active loop state engine (LHS seed generator -> GP Fit -> Suggest)
│   │   ├── equipment_db.py         # Static physical parameters for lab & industrial granulators
│   │   ├── scaling_laws.py         # Dimensonless Froude, Tip Speed, and Reynolds calculations
│   │   ├── hybrid_twin.py          # Dimensonless mechanistic scale-up coupled with ML corrector prediction
│   │   ├── residual_corrector.py   # Machine learning correction model loading and inference
│   │   ├── risk_map.py             # Active Loop convergence risk and zoning engine
│   │   └── design_space.py         # Locked operating ranges reconciled with stress thresholds
│   ├── routers/
│   │   ├── v1_bayesian_doe.py      # Active Learning endpoints (/domain, /experiments/result, /suggest, /summary)
│   │   ├── v2_scaleup.py           # Scale-Up Digital Twin simulator endpoints (/scaleup)
│   │   └── v3_risk.py              # Risk audit and GMP failure mode evaluator
│   ├── models/
│   │   └── v2_residual_corrector.pkl # Pre-trained ML corrector Random Forest estimator
│   └── tests/                      # Pytest validation suites
│       ├── test_v1_bo.py           # Core bounds validation checks
│       ├── test_v1_bo_botorch.py   # active BoTorch simulation tests
│       ├── test_v1_phase1_integration.py # Phase 1 integration schema verification
│       ├── test_v1_router.py       # Active Learning API routing and handler verification
│       └── test_v2_scaleup.py      # Digital Twin Scaleup mechanistic + endpoint validation tests
├── data/                           # Historical research datasets (Alpha, Beta, dummy, etc.)
│   ├── Final Dataset.json
│   ├── team alpha finalised dummy dataset.json
│   └── team beta finalised dummy dataset.json
└── frontend/
    ├── src/
    │   ├── App.jsx                 # Main application UI and multi-tab system layout
    │   └── components/
    │         ├── Vector1/
    │         │     └── ActiveLearningDashboard.jsx  # Active Learning interface with loop status & export
    │         └── Vector2/
    │               └── ScaleUpDashboard.jsx         # Physical Scale-Up digital twin simulator dashboard
```

---

## ⚡ Unified Vector Features

### 🔬 Vector 1: Bayesian Active Learning Engine
- **LHS Seed Initialization**: Generates **8 space-filling seed experiments** using Latin Hypercube Sampling (LHS) to initially seed the design space.
- **Mass-Balance Constraint Solver**: Restricts total excipient w/w concentrations to $\le 70\%$, maintaining a $30\%$ minimum margin for the active drug substance.
- **Physics-Informed Dynamic Bounds**: Adapts process parameter search spaces dynamically by calculating safe boundaries relative to API thermal limits:
  $$\text{Max Temp} = \min(100.0^\circ\text{C}, T_{\text{decomposition}} - 15^\circ\text{C}, T_{g} - 7^\circ\text{C}, T_{g,\text{excipient}} - 5^\circ\text{C})$$
- **8-CQA Multi-Objective GP**: Fits 8 independent Gaussian Process models using Matérn kernels ($\nu = 2.5$).
- **Optimized `qLogNEHVI` Suggestions**: Evaluates expected hypervolume improvement using a standard scikit-learn fallback layer to guarantee uptime.
- **Audited Convergence HUD**: Monitors hypervolume indicators across rounds and reports flatline convergence ($\Delta HV < 0.01$, patience = 3).
- **Handoff Export (JSON)**: Features a single-click button to download validated active loop summaries matching `phase1_output.json`.

### ⚙️ Vector 2: Digital Twin Scale-Up Simulator
- **Multi-Granulator Equipment Database**: Stores geometries, volume capacities, impeller diameters, and maximum limits for both laboratory ($10\text{ L}$) and commercial ($300\text{ L}$) fluid-bed/granulation systems.
- **Mechanistic Dimensionless Scaling**: Scales process parameters (RPM, spray rate, batch size) between equipment sizes using:
  * **Froude Similarity ($Fr$)**: Scales impeller rotational speed to maintain equivalent physical liquid distributions.
  * **Tip Speed ($v_{tip}$)**: Computes alternative shear boundaries.
- **Machine Learning Residual Corrector**: Loads a pre-trained Random Forest model (`v2_residual_corrector.pkl`) that corrects the theoretical scaling rules for physical micro-granulation interactions.
- **Turbulence Validation**: Computes output Reynolds numbers ($Re$) and issues a warning banner if flow transitions out of the turbulent regime ($Re < 10,000$).
- **Industrial Adjustments**: Automatically applies a standard 15% safety increase to tablet compression force parameters during commercial scale runs.

---

## 🛠️ Installation & Setup

Ensure you have a Python environment and Node.js installed on your host.

### 1. Backend Setup (FastAPI & PyTorch)
A configured Python 3.10 virtual environment is available under `/home/harshit/vector_1_p/backend/venv/`. To activate and verify it:

```bash
# Navigate to backend folder
cd backend/

# Activate the virtual environment
source venv/bin/activate

# Install dependencies (including testing tools)
pip install -r requirements.txt
pip install httpx
```

### 2. Frontend Setup (React & Vite)
The React front-end dashboard is located in `frontend/`. To run it:

```bash
# Navigate to the frontend directory
cd frontend/

# Start Vite server
npm run dev
```

---

## 🚀 Running the Services

### 1. Launch FastAPI Backend
```bash
cd backend/
PYTHONPATH=. venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```
The REST API is live at `http://localhost:8001`. Interactive Swagger endpoints are viewable at `http://localhost:8001/docs`.

### 2. Launch Vite Frontend Dashboard
```bash
cd frontend/
npm run dev
```
The React development server is live at `http://localhost:5173`.

### 3. Port Forwarding for External Access (MacBook Air to VM)
Execute the secure SSH port-forwarding command on your local Mac machine:
```bash
gcloud compute ssh enformis-gpu-instance \
  --zone=asia-south1-b \
  --project=ultra-472304 \
  -- -L 5173:localhost:5173 -L 8001:localhost:8001
```
Now, open your Mac web browser and explore the platform at `http://localhost:5173/`.

---

## 🧪 Comprehensive Testing Suite

We maintain a rigorous engineering quality gate using the `pytest` test framework.

To execute the full suite of **11 tests** (covering Vector 1, Vector 2, and router serialize endpoints):

```bash
cd backend/
PYTHONPATH=. venv/bin/pytest tests/
```

### What gets verified:
1.  🔬 **`tests/test_v1_bo.py`**: Validates basic physics boundaries and dynamic design constraint calculations.
2.  📡 **`tests/test_v1_router.py`**: Verifies input serialization and model response formats of active Bayesian routes.
3.  🎲 **`tests/test_v1_bo_botorch.py`**: Simulates the complete active learning loop (generating 8 LHS seeds, submitting outcomes, training GPs, evaluating EHVI, and suggesting iterations).
4.  📊 **`tests/test_v1_phase1_detailed.py` & `test_v1_phase1_integration.py`**: Reconciles and parses the baseline output datasets for BCS Class-I API profiles.
5.  ⚙️ **`tests/test_v2_scaleup.py`**: Specifically exercises the digital twin, ensuring Froude calculations, equipment geometries, and Random Forest corrector predictions produce physically-realistic operational values.
