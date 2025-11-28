from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import (Apartment,
                                                                       Session,
                                                                       PersonalData,
                                                                       Tenancy,
                                                                       Contract)

def get_apartments() -> list[Apartment]:
    session = None
    try:
        session = Session()
        # Get all apartment data
        apartments = session.query(Apartment).all()

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_APARTMENTS, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_APARTMENTS, trace_id) from error
    finally:
        if session:
            session.close()
    return apartments
    """
    # Get all data sorted by ...
    personal_data = session.query(PersonalData)
    ordered_personal_data_by_name = personal_data.order_by(asc(PersonalData.first_name))
    get_data = ordered_personal_data_by_name.all()
    
    for personal_data in get_data:
        print(personal_data)
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

def get_single_person(*,first_name: str, last_name: str, id_personal_data: int) -> PersonalData:
    session = None

    try:
        session = Session()
        query = session.query(PersonalData)

        # Build dynamic filtering based on provided identifiers.
        # If only ID is provided -> filter by ID.
        # If only first_name/last_name -> filter by those.
        # If all are provided -> filter by all three.

        filters = []

        # id_personal_data may come as None or an empty/zero-like value if not used.
        if id_personal_data not in (None, "", 0):
            filters.append(PersonalData.id_personal_data == id_personal_data)

        if first_name:
            filters.append(PersonalData.first_name == first_name)

        if last_name:
            filters.append(PersonalData.last_name == last_name)

        if not filters:
            trace_id = log_error(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_PERSON)
            raise APIError(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_PERSON, trace_id)

        person = query.filter(*filters).one()
        return person
    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_SINGLE_PERSON, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_SINGLE_PERSON, trace_id) from error
    finally:
        if session:
            session.close()


def get_persons() -> list[PersonalData]:
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

def get_tenancies() -> list[Tenancy]:
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


def get_contract() -> list[Contract]:
    session = None
    try:
        session = Session()
        contracts = session.query(Contract).all()

        return contracts

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_CONTRACTS, error)
        raise APIError(ErrorCode.SQL_ERROR_READING_ENTRY_FOR_ALL_CONTRACTS, trace_id) from error
    finally:
        if session:
            session.close()

def get_single_apartment(*, address: str = None, id_apartment: int = None) -> Apartment:
    session = None
    try:
        session = Session()
        query = session.query(Apartment)
        filters = []

        if id_apartment not in (None, "", 0):
            filters.append(Apartment.id_apartment == id_apartment)
        
        if address:
            filters.append(Apartment.address == address)

        if not filters:
            trace_id = log_error(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_APARTMENT) # Assuming error code
            raise APIError(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_APARTMENT, trace_id)

        apartment = query.filter(*filters).one()
        return apartment
    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_SINGLE_APARTMENT, error) # Assuming error code
        raise APIError(ErrorCode.SQL_ERROR_READING_SINGLE_APARTMENT, trace_id) from error
    finally:
        if session:
            session.close()

def get_single_tenancy(*, id_tenancy: int = None) -> Tenancy:
    session = None
    try:
        session = Session()
        query = session.query(Tenancy)
        filters = []

        if id_tenancy not in (None, "", 0):
            filters.append(Tenancy.id_tenancy == id_tenancy)

        if not filters:
            trace_id = log_error(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_TENANCY) # Assuming error code
            raise APIError(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_TENANCY, trace_id)

        tenancy = query.filter(*filters).one()
        return tenancy
    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_SINGLE_TENANCY, error) # Assuming error code
        raise APIError(ErrorCode.SQL_ERROR_READING_SINGLE_TENANCY, trace_id) from error
    finally:
        if session:
            session.close()

def get_single_contract(*, id_contract: int = None) -> Contract:
    session = None
    try:
        session = Session()
        query = session.query(Contract)
        filters = []

        if id_contract not in (None, "", 0):
            filters.append(Contract.id_contract == id_contract)

        if not filters:
            trace_id = log_error(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_CONTRACT) # Assuming error code
            raise APIError(ErrorCode.SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_CONTRACT, trace_id)

        contract = query.filter(*filters).one()
        return contract
    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_READING_SINGLE_CONTRACT, error) # Assuming error code
        raise APIError(ErrorCode.SQL_ERROR_READING_SINGLE_CONTRACT, trace_id) from error
    finally:
        if session:
            session.close()
