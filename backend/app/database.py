from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """Add any model columns missing from already-existing tables.

    Base.metadata.create_all only creates tables that don't exist yet, so a
    table created by an earlier version of a model never picks up new
    columns. This project has no Alembic migration chain, so this is a
    minimal additive-only patch step run at startup.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(
                    text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}")
                )
                if column.default is not None and column.default.is_scalar:
                    conn.execute(
                        text(
                            f"UPDATE {table.name} SET {column.name} = :default "
                            f"WHERE {column.name} IS NULL"
                        ),
                        {"default": column.default.arg},
                    )
