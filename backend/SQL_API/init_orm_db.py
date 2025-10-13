from ApartmentManager.backend.SQL_API.rentral.rental_orm_models import Rental_Base, rental_engine
from ApartmentManager.backend.SQL_API.logs.logs_orm_models import Log_Base, log_engine


#TODO at the moment start the DB initialisation manually. Later automatically

# create tables with rental information
Rental_Base.metadata.create_all(rental_engine)

# create table for logging the AI conversation
Log_Base.metadata.create_all(log_engine)