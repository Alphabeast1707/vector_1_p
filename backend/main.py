from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import v1_bayesian_doe

app = FastAPI(
    title="EnFormis Module 3 API",
    description="Manufacturing Intelligence Core for EnFormis Platform",
    version="2.0.0"
)

# Enable CORS for frontend interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "EnFormis Module 3 Backend is running"}

# Register Vector 1 Active Learning router
app.include_router(v1_bayesian_doe.router)