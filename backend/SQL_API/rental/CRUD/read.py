import traceback
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import (Apartment,
                                                                       Session,
                                                                       PersonalData,
                                                                       Tenancy,
                                                                       Contract)

def get_apartments():
    session = Session()
    apartments = None
    try:
        # Get all apartment data
        apartments = session.query(Apartment).all()
        """
        # Get all data sorted by ...
        personal_data = session.query(PersonalData)
        ordered_personal_data_by_name = personal_data.order_by(asc(PersonalData.first_name))
        get_data = ordered_personal_data_by_name.all()
        
        for personal_data in get_data:
            print(personal_data)
        """

        """
        # Get single row by known value
        Anna = session.query(PersonalData).filter(PersonalData.first_name == 'Anna').one()
        print(Anna)
        """

        """
        # Get all rows by known value
        apartments = session.query(Apartment).filter(Apartment.area ==  85.5).all()
        for apartment in apartments:
            print(apartment)
        """

        """
        # Get rows using filter with boolean logic
        apartments = (session.query(Apartment)
            .filter(or_(Apartment.price_per_square_meter == 14.5, Apartment.price_per_square_meter == 16.3))
            .all())
        for apartment in apartments:
            print(apartment)
        """
        """
            # Get person with the Last name starting with ...
            persons = session.query(PersonalData).filter(PersonalData.last_name.ilike("%ler%")).all()
            for person in persons:
                print(person)
            session.commit()
        """
    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    return apartments

def get_persons():
    session = Session()
    persons = None
    try:
        persons = session.query(PersonalData).all()
    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    return persons

def get_tenancies():
    session = Session()
    tenancies = None
    try:
        tenancies = session.query(Tenancy).all()
    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    return tenancies

def get_contract():
    session = Session()
    rent_data = None
    try:
        rent_data = session.query(Contract).all()
    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
    return rent_data