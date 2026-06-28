from fastapi import FastAPI
from app.api.product import router as product_router
from app.api.execute import router as execute_router
from app.api.agent import router as agent_router

app = FastAPI(title="Product Center")

app.include_router(product_router)
app.include_router(execute_router)
app.include_router(agent_router)
