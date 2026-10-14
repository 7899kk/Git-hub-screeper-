from alembic import context
from pulse_api.storage import Base, database

engine, _ = database()
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
