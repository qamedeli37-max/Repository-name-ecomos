from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.product import Product, ProductCreate
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.db.database import SessionLocal

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)):
    repo = ProductRepository(db)
    return ProductService(repo)


@router.get("", response_model=list[Product])
def list_products(service: ProductService = Depends(get_service)):
    return service.list()


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str, service: ProductService = Depends(get_service)):
    product = service.get({"id": product_id})
    if not product or "error" in product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=Product, status_code=201)
def create_product(body: ProductCreate, service: ProductService = Depends(get_service)):
    return service.create(body.model_dump())


@router.delete("/{product_id}")
def delete_product(product_id: str, service: ProductService = Depends(get_service)):
    if not service.delete(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}
