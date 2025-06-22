from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import Base, engine
from routers import users, files, extracted
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Management API")

# CORS settings as frontend is separate
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

@app.get("/check", tags=["health"])
def root():
    return {"message": "API is running"}
