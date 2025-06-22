from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from routers import users, files, extracted
import uvicorn
import os

# Initialize FastAPI app
app = FastAPI(title="Invoice Management API")

# CORS settings for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router)
app.include_router(files.router)
app.include_router(extracted.router)

# Health check endpoint
@app.get("/check", tags=["health"])
def root():
    return {"message": "API is running"}

# Move DB table creation to here, inside __main__ for dev only
if __name__ == "__main__":
    # Create database tables for local dev only
    Base.metadata.create_all(bind=engine)

    port = int(os.environ.get("PORT", 8000))  # Default to 8000 locally
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
