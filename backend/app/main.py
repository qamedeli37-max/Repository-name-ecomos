from fastapi import FastAPI
from app.api.product import router as product_router

app = FastAPI(title="Product Center")

app.include_router(product_router)
