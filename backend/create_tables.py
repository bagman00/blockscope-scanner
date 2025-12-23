from app.core.database import engine, Base

# This creates all tables defined in your models
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")