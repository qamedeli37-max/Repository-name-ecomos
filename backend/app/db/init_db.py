from app.db.database import engine, Base
from app.db.models.product import ProductORM  # noqa: F401
from app.db.models.execution import ExecutionLogORM  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
