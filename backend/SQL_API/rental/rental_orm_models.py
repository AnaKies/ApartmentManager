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

    @staticmethod
    def fields_dict():
        """
        Used to get all class fields as string without creating a class object.
        :return:
        """
        return {
            "area": None,
            "address": None,
            "price_per_square_meter": None,
            "utility_billing_provider_id": None
        }

    @staticmethod
    def required_fields_to_create():
        return {
            "address": None,
        }

    @staticmethod
    def fields_dict_for_update():
        """
        Used to get all fields required for updating an apartment.
        Includes both identifier fields (to find the apartment) and update fields (to update the apartment).
        :return: Dictionary with all fields needed for update_apartment() function
        """
        return {
            "old_address": None,
            "id_apartment": None,
            "area": None,
            "address": None,
            "price_per_square_meter": None,
            "utility_billing_provider_id": None
        }

    @staticmethod
    def required_fields_to_delete():
        return {"first_possibility": ["id_apartment"],
                "second_possibility": ["address"]}

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

    @staticmethod
    def fields_dict():
        """
        Used to get all class fields as string without creating a class object.
        :return:
        """
        return {
            "id_apartment": None,
            "id_tenant_personal_data": None,
            "id_contract": None,
            "move_in_date": None,
            "move_out_date": None,
            "deposit": None,
            "registered_address": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_create():
        return {
            "move_in_date": None,
            "registered_address": None,
        }

    @staticmethod
    def fields_dict_for_update():
        """
        Used to get all fields required for updating a tenancy.
        Includes both identifier fields (to find the tenancy) and update fields (to update the tenancy).
        :return: Dictionary with all fields needed for update_tenancy() function
        """
        return {
            "id_tenancy": None,
            "id_apartment": None,
            "id_tenant_personal_data": None,
            "id_contract": None,
            "move_in_date": None,
            "move_out_date": None,
            "deposit": None,
            "registered_address": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_delete():
        return {"first_possibility": "id_apartment",
                "second_possibility": "id_tenancy",
                "third_possibility": "id_tenant_personal_data"}

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

    @staticmethod
    def fields_dict():
        """
        Used to get all class fields as string without creating a class object.
        :return:
        """
        return {
            "first_name": None,
            "last_name": None,
            "bank_data": None,
            "phone_number": None,
            "email": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_create():
        return {
            "first_name": None,
            "last_name": None
        }

    @staticmethod
    def fields_dict_for_update():
        """
        Used to get all fields required for updating a person.
        Includes both identifier fields (to find the person) and update fields (to update the person).
        :return: Dictionary with all fields needed for update_person() function
        """
        return {
            "old_first_name": None,
            "old_last_name": None,
            "id_personal_data": None,
            "first_name": None,
            "last_name": None,
            "bank_data": None,
            "phone_number": None,
            "email": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_delete():
        return {"first_possibility": ["id_personal_data"],
                "second_possibility": ["first_name", "last_name"]}

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

    @staticmethod
    def fields_dict():
        """
        Used to get all class fields as string without creating a class object.
        :return:
        """
        return {
            "net_rent": None,
            "utility_costs": None,
            "vat": None,
            "garage": None,
            "parking_spot": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_create():
        return {
            "net_rent": None,
        }

    @staticmethod
    def fields_dict_for_update():
        """
        Used to get all fields required for updating a contract.
        Includes both identifier fields (to find the contract) and update fields (to update the contract).
        :return: Dictionary with all fields needed for update_contract() function
        """
        return {
            "id_contract": None,
            "net_rent": None,
            "utility_costs": None,
            "vat": None,
            "garage": None,
            "parking_spot": None,
            "comment": None
        }

    @staticmethod
    def required_fields_to_delete():
        return {"first_possibility": "id_contract"}