import traceback

from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import (Apartment,
                                                                       Session,
                                                                       PersonalData,
                                                                       Tenancy,
                                                                       Contract)

def get_apartments():
    session = None
    try:
        session = Session()
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
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_APARTMENTS, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_APARTMENTS, trace_id) from error
    finally:
        if session:
            session.close()
    return apartments

def get_persons():
    session = None

    try:
        session = Session()
        persons = session.query(PersonalData).all()
        return persons
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_PERSONS, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_PERSONS, trace_id) from error
    finally:
        if session:
            session.close()

def get_tenancies():
    session = Session()

    try:
        tenancies = session.query(Tenancy).all()
        return tenancies
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_TENANCIES, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_TENANCIES, trace_id) from error
    finally:
        if session:
            session.close()


def get_contract():
    session = None
    try:
        session = Session()
        rent_data = session.query(Contract).all()
        return rent_data
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_CONTRACTS, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_CONTRACTS, trace_id) from error
    finally:
        if session:
            session.close()
