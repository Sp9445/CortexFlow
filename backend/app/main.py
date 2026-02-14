from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import models so that they are registered with SQLAlchemy metadata
from app.models import user, diary_entry, refresh_token

# Import routers
from app.routes import auth, diary, ai


app = FastAPI(
    title="CortexFlow API",
    version="1.0.0"
)

# ----------------------------
# CORS Configuration
# ----------------------------

origins = [
    "http://localhost:4200",  # Angular dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Include Routers
# ----------------------------

app.include_router(auth.router)
app.include_router(diary.router)
app.include_router(ai.router)


# ----------------------------
# Health Check
# ----------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}
