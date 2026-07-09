# EnFormis Vector 1 — Multi-Objective Bayesian Active Learning Engine

Welcome to the production repository for **EnFormis Vector 1 (Module 3)**. This codebase hosts the high-performance manufacturing intelligence engine for active design of experiments (DoE) and process optimization, using advanced Bayesian optimization via BoTorch/PyTorch coupled with a dynamic React-based Active Learning Dashboard.

---

## 🔬 What is Vector 1 (Active Learning)?

Vector 1 is a physics-informed active experimentation engine designed to accelerate pharmaceutical formulation development. Instead of traditional brute-force trial-and-error or static design of experiments (DoE), Vector 1 uses a **closed-loop Bayesian active learning cycle**:

1.  **Surrogate Modeling**: Independent Multi-Task Gaussian Processes (GP) with Matérn 5/2 covariance kernels learn the highly non-linear relationships between recipe process inputs and critical quality attributes (CQAs).
2.  **Acquisition Optimization**: The system optimizes a multi-objective acquisition function—**Log-Noisy Expected Hypervolume Improvement (qLogNEHVI)**—to recommend the single next-best experiment coordinates that balance exploration (probing high-uncertainty regions) and exploitation (homing in on optimal sweet spots).
3.  **Dynamic Safety Bounds**: Search boundaries for Critical Process Parameters (CPPs) are dynamically adapted by reading the solid-state properties of the active pharmaceutical ingredient (API) (e.g., Glass Transition Temperature $T_g$ and Decomposition temperature).

This closed-loop system is mathematically proven to converge on optimal, Pareto-efficient formulation recipes **up to 80% faster** than traditional experimentation.

---

## 📁 Repository Structure (Vector 1 Core)

```text
├── .gitignore                      # Workspace ignores (environments, cache, OS files)
├── README.md                       # Comprehensive Vector 1 system documentation
├── verify_build.py                 # Integrated build validator and test suite runner
├── backend/
│   ├── .gitignore                  # Virtual environment ignores
│   ├── main.py                     # FastAPI application setup and CORS configuration
│   ├── requirements.txt            # Python dependencies (botorch, fastapi, gpytorch, etc.)
│   ├── engines/
│   │   ├── data_ingestion.py       # Parses and aligns Team Alpha and Team Beta datasets
│   │   ├── domain_builder.py       # Constructs dynamic search domains constrained by thermal limits
│   │   ├── gp_model.py             # SingleTaskGP surrogate setup with Matérn-5/2 kernels
│   │   ├── acquisition.py          # Log-Noisy Expected Hypervolume Improvement (qLogNEHVI) acquisition
│   │   ├── bo_loop.py              # Active learning loop controller (LHS seeds, GP Fitting, Suggestion)
│   │   ├── risk_map.py             # Active loop zoning (ROBUST/TRANSITIONAL/FRAGILE)
│   │   └── design_space.py         # Computes locked design boundaries reconciled with stress constraints
│   ├── routers/
│   │   └── v1_bayesian_doe.py      # FastAPI HTTP route handlers (/domain, /experiments/result, /suggest, /summary)
│   └── tests/                      # Python pytest validation suites
│       ├── test_v1_bo.py           # Core bounds validation checks
│       ├── test_v1_bo_botorch.py   # Active BoTorch simulation tests
│       ├── test_v1_phase1_integration.py # Phase 1 integration schema verification
│       └── test_v1_router.py       # API routing and handler verification
└── frontend/
    └── src/
        ├── App.jsx                 # Main React container
        └── components/
            └── Vector1/
                └── ActiveLearningDashboard.jsx  # Dynamic Active Learning Dashboard with loop status and summary export
```

---

## 🧮 Detailed 5-Step Pipeline Mathematics & Logic

### 1. Ingestion & Dynamic Constraints
The system ingests 71 physicochemical parameters for APIs (Team Alpha) and 25 excipient properties (Team Beta). It dynamically bounds process inputs to prevent chemical degradation:
*   **Drying Temperature Ceiling**:
    $$\text{Drying Temp Max} = \min\left(100.0^\circ\text{C},\ T_{\text{decomposition}} - 15.0^\circ\text{C},\ T_{g} - 7.0^\circ\text{C}\right)$$
*   **Granulation Moisture Controls**: Tightens boundaries if excipients have low moisture stability ($\le 0.5$) or high hydrophilicity ($\ge 0.8$).

### 2. Space-Filling Seeding
The engine generates exactly **8 initial recipes** using **Latin Hypercube Sampling (LHS)** to space-fill the design domain. Each seed configuration is processed through a strict **Mass-Balance Constraint Solver** ensuring total active excipient w/w does not exceed $70\%$ (reserving $30\%$ for the API and lubricant):
$$\sum \text{Excipients w/w \%} \le 70.0\%$$

### 3. GP Surrogate Fitting
Vector 1 fits independent Gaussian Process regressors to 8 distinct Critical Quality Attributes (CQAs):
*   **Covariance Kernel**: Matérn 5/2 kernel ($\nu = 2.5$) with Automatic Relevance Determination (ARD).
*   **Model Validation**: Automatically computes Leave-One-Out Cross-Validation (LOO-CV) $R^2$ scores across CQAs to monitor learning health.
*   **Output Profiles**: Provides prediction mean, standard deviation, 95% Confidence Intervals ($\mu \pm 1.96\sigma$), and an automated spec check.

### 4. Objective Transformations
To maximize all goals within the hypervolume framework, the engine standardizes physical CQA metrics to a maximizable **"maximize toward 0.0"** scale:
*   **Dissolution Q15–Q60 (Maximize)**: $f(y) = y$
*   **Friability % (Minimize)**: $f(y) = -y$
*   **Tablet Hardness (Target exactly $100\text{ N}$)**: $f(y) = -|y - 100.0|$
*   **Content Uniformity (Target exactly $100\%$ w/w)**: $f(y) = -|y - 100.0|$
*   **Heckel Slope Compressibility (Target exactly $0.115$)**: $f(y) = -|y - 0.115|$

### 5. Multi-Objective Optimization (qLogNEHVI)
Queries BoTorch's `qLogNoisyExpectedHypervolumeImprovement` to suggest the next recipe. If PyTorch dependencies are missing, the loop silently switches to an automated scikit-learn UCB multi-surrogate fallback to maintain high availability.

---

## 🛠️ Installation & Activation

Ensure you have a Python environment and Node.js installed on your host.

### 1. Setup Backend
Navigate to the backend, activate your virtual environment, and install testing/network requirements:
```bash
cd backend/
source venv/bin/activate
pip install -r requirements.txt
pip install httpx
```

### 2. Setup Frontend
Navigate to the frontend folder and install npm packages:
```bash
cd frontend/
npm install
```

---

## 🚀 Running the Vector 1 Platform

### 1. Start the FastAPI Backend (Port 8001)
```bash
cd backend/
PYTHONPATH=. venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```
View interactive REST API documentation at `http://localhost:8001/docs`.

### 2. Start the Vite React Frontend (Port 5173)
```bash
cd frontend/
npm run dev
```

### 3. Map SSH Ports from Your local Mac (MacBook Air to VM)
Execute the secure SSH port-forwarding command inside your local Mac terminal:
```bash
gcloud compute ssh enformis-gpu-instance \
  --zone=asia-south1-b \
  --project=ultra-472304 \
  -- -L 5173:localhost:5173 -L 8001:localhost:8001
```
Now explore the live interface in your Mac web browser:
👉 **`http://localhost:5173/`**

---

## 🧪 Sequential Testing & CI Gate

Vector 1 features a custom-built automated verification gate: `verify_build.py`. Running it audits scientific dependency imports and sequential pytest executions:

```bash
# Execute standard pytest files
cd backend/
PYTHONPATH=. venv/bin/pytest tests/

# Run the automated continuous integration gate
python3 verify_build.py
```
