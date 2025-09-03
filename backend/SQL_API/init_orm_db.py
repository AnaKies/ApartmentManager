from ApartmentManager.backend.SQL_API.orm_models import Base, engine

Base.metadata.create_all(engine)