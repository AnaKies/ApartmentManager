import os

from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Define a path to the database
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DB_PATH = os.path.join(BASE_DIR, "data", "apartment_app.db")

# Create a database connection
rental_engine = create_engine(f'sqlite:///{DB_PATH}',
                              connect_args={'check_same_thread': False, "timeout": 15},
                              echo=True)

# Create a database session (performs CRUD operations with ORM objects)
Session = sessionmaker(bind=rental_engine) # returns Fabric

# Define the data table class's parent class
Rental_Base = declarative_base()

class Apartment(Rental_Base):
    __tablename__ = "apartment"
    # manual id for fixed number of apartments
    id_apartment = Column(Integer, primary_key=True, autoincrement=True)
    area = Column(Float)
    address = Column(String)
    price_per_square_meter = Column(Float)
    utility_billing_provider_id = Column(Integer)

    def __repr__(self):
        return (f"Apartment ("
                f"id_apartment={self.id_apartment}, "
                f"area={self.area}, "
                f"address={self.address}, "
                f"price_per_square_meter={self.price_per_square_meter}, "
                f"utility_billing_provider_id={self.utility_billing_provider_id})")

    def to_dict(self):
        return {
            "id_apartment": self.id_apartment,
            "area": self.area,
            "address": self.address,
            "price_per_square_meter": self.price_per_square_meter,
            "utility_billing_provider_id": self.utility_billing_provider_id
        }


class Tenancy(Rental_Base):
    __tablename__ = "tenancy"
    # automatically autoincrement for infinity number of tenancies
    id_tenancy = Column(Integer, primary_key=True, autoincrement=True)
    id_apartment = Column(Integer)
    id_tenant_personal_data = Column(Integer)
    id_contract = Column(Integer)
    move_in_date = Column(String)
    move_out_date = Column(String)
    deposit = Column(Float)
    registered_address = Column(String)
    comment = Column(String)

    def __repr__(self):
        return (f"Tenancy ("
                f"id_tenancy={self.id_tenancy}, "
                f"id_apartment={self.id_apartment}, "
                f"id_tenant_personal_data={self.id_tenant_personal_data}, "
                f"id_contract={self.id_contract}, "
                f"move_in_date={self.move_in_date}, "
                f"move_out_date={self.move_out_date}, "
                f"deposit={self.deposit}, "
                f"registered_address={self.registered_address}, "
                f"comment={self.comment})")

    def to_dict(self):
        return {
            "id_tenancy": self.id_tenancy,
            "id_apartment": self.id_apartment,
            "id_tenant_personal_data": self.id_tenant_personal_data,
            "id_contract": self.id_contract,
            "move_in_date": self.move_in_date,
            "move_out_date": self.move_out_date,
            "deposit": self.deposit,
            "registered_address": self.registered_address,
            "comment": self.comment
        }


class PersonalData(Rental_Base):
    __tablename__ = "personal_data"
    # automatically autoincrement for infinity number of persons
    id_personal_data = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    bank_data = Column(String)
    phone_number = Column(String)
    email = Column(String)
    comment = Column(String)

    def __repr__(self):
        return (f"Personal Data ("
                f"id_personal_data={self.id_personal_data}, "
                f"first_name={self.first_name}, "
                f"last_name={self.last_name}, "
                f"bank_data={self.bank_data}, "
                f"phone_number={self.phone_number}, "
                f"email={self.email}, "
                f"comment={self.comment})")

    def to_dict(self):
        return {
            "id_personal_data": self.id_personal_data,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bank_data": self.bank_data,
            "phone_number": self.phone_number,
            "email": self.email,
            "comment": self.comment
        }


class Contract(Rental_Base):
    __tablename__ = "contract"
    # automatically autoincrement for infinity number of rents
    id_contract = Column(Integer, primary_key=True, autoincrement=True)
    net_rent = Column(Float)
    utility_costs = Column(Float)
    vat = Column(Float)
    garage = Column(Float)
    parking_spot = Column(Float)
    comment = Column(String)

    def __repr__(self):
        return (f"Contract ("
                f"id_contract={self.id_contract}, "
                f"net_rent={self.net_rent}, "
                f"utility_costs={self.utility_costs}, "
                f"vat={self.vat}, "
                f"garage={self.garage}, "
                f"parking_spot={self.parking_spot}, "
                f"comment={self.comment})")

    def to_dict(self):
        return {
            "id_contract": self.id_contract,
            "net_rent": self.net_rent,
            "utility_costs": self.utility_costs,
            "vat": self.vat,
            "garage": self.garage,
            "parking_spot": self.parking_spot,
            "comment": self.comment
        }