from fastapi import FastAPI
from app.api.product import router as product_router
from app.api.execute import router as execute_router
from app.api.agent import router as agent_router
from app.api.execution import router as execution_router
from app.api.admin import router as admin_router
from app.db.init_db import init_db

app = FastAPI(title="Product Center")

app.include_router(product_router)
app.include_router(execute_router)
app.include_router(agent_router)
app.include_router(execution_router)
app.include_router(admin_router)

@app.on_event("startup")
def startup():
    init_db()
