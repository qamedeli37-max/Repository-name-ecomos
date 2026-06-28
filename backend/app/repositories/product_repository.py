import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.product import Product, ProductCreate
from app.db.models.product import ProductORM


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ProductCreate) -> Product:
        orm = ProductORM(
            id=str(uuid.uuid4()),
            title=data.title,
            price=data.price,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        return self._to_pydantic(orm)

    def get(self, product_id: str) -> Product | None:
        orm = self.db.query(ProductORM).filter(ProductORM.id == product_id).first()
        return self._to_pydantic(orm) if orm else None

    def list(self) -> list[Product]:
        rows = self.db.query(ProductORM).all()
        return [self._to_pydantic(r) for r in rows]

    def delete(self, product_id: str) -> bool:
        orm = self.db.query(ProductORM).filter(ProductORM.id == product_id).first()
        if not orm:
            return False
        self.db.delete(orm)
        self.db.commit()
        return True

    @staticmethod
    def _to_pydantic(orm: ProductORM) -> Product:
        return Product(
            id=orm.id,
            title=orm.title,
            subtitle=orm.subtitle or "",
            description=orm.description or "",
            price=orm.price,
            currency=orm.currency,
            stock=orm.stock,
            created_at=orm.created_at.isoformat(),
            updated_at=orm.updated_at.isoformat(),
        )
