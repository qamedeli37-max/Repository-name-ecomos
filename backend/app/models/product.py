from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    description: str = ""
    price: float
    currency: str = "CNY"
    stock: int = 0
    created_at: str = ""
    updated_at: str = ""


class ProductCreate(BaseModel):
    title: str
    price: float
