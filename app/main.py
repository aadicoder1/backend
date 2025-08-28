from fastapi import FastAPI
from app.database import Base, engine
from app.models import user
from app.routes import user as user_routes
from app.routes import auth as auth_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KMRL SmartDocs Backend")

# include routes
app.include_router(user_routes.router)
app.include_router(auth_routes.router)

@app.get("/")
def root():
    return {"msg": "Backend running with PostgreSQL 🚀"}
