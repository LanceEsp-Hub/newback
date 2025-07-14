from logging.config import fileConfig
import os
from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Alembic Config object
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models
from app.database import Base
from backend.app.models.models import User  # Import all your models here

# Set metadata for autogenerate
target_metadata = Base.metadata

# Use DATABASE_URL from .env file
url = os.getenv("DATABASE_URL")

# Debugging: Print database URL (remove this later)
print(f"Using DATABASE_URL: {url}")

if not url:
    raise ValueError("Error: DATABASE_URL is not set. Check your .env file.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
