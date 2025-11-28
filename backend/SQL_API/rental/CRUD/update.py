from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Session, Apartment, Tenancy, Contract

def update_person(
                    old_first_name: str,
                    old_last_name: str,
                    id_personal_data: int,
                    first_name: str,
                    last_name: str,
                    bank_data: str,
                    phone_number: str,
                    email: str,
                    comment: str) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_personal_data not in (None, "")
        name_given = old_first_name not in (None, "") and old_last_name not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given and not name_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_UPDATING_ENTRY)

        session = Session()

        # filter by personal ID
        if id_given:
            query = session.query(PersonalData).filter(
                PersonalData.id_personal_data == id_personal_data
            )
        else: # filter by first name and last name
            query = session.query(PersonalData).filter(
                PersonalData.first_name == old_first_name,
                PersonalData.last_name == old_last_name
            )

        # try to get the person to update
        person = query.one_or_none()

        if person is None:
            raise APIError(ErrorCode.SQL_SUCH_PERSON_DOES_NOT_EXIST)

        # update person with new data
        if first_name not in (None, ""):
            person.first_name = first_name

        if last_name not in (None, ""):
            person.last_name = last_name

        if bank_data not in (None, ""):
            person.bank_data = bank_data

        if phone_number not in (None, ""):
            person.phone_number = phone_number

        if email not in (None, ""):
            person.email = email

        if comment not in (None, ""):
            person.comment = comment

        if person:
            # save the data of the person, that will be deleted in the next step
            person_data = person.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_PERSON_DOES_NOT_EXIST)
            raise APIError(ErrorCode.SQL_SUCH_PERSON_DOES_NOT_EXIST, trace_id)

        session.commit()

        return person_data

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON, error)
        raise APIError(ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON, trace_id) from error
    finally:
        if session:
            session.close()

def update_apartment(
                    old_address: str,
                    id_apartment: int,
                    area: float,
                    address: str,
                    price_per_square_meter: float,
                    utility_billing_provider_id: int) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_apartment not in (None, "")
        address_given = old_address not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given and not address_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_UPDATING_ENTRY)

        session = Session()

        # filter by personal ID
        if id_given:
            query = session.query(Apartment).filter(
                Apartment.id_apartment == id_apartment
            )
        else: # filter by first name and last name
            query = session.query(Apartment).filter(
                Apartment.address == old_address
            )

        # try to get the person to update
        apartment = query.one_or_none()

        if apartment is None:
            raise APIError(ErrorCode.SQL_SUCH_APARTMENT_DOES_NOT_EXIST) # Assuming error code

        # update person with new data
        if area not in (None, ""):
            apartment.area = area

        if address not in (None, ""):
            apartment.address = address

        if price_per_square_meter not in (None, ""):
            apartment.price_per_square_meter = price_per_square_meter

        if utility_billing_provider_id not in (None, ""):
            apartment.utility_billing_provider_id = utility_billing_provider_id

        if apartment:
            # save the data of the person, that will be deleted in the next step
            apartment_data = apartment.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_APARTMENT_DOES_NOT_EXIST)
            raise APIError(ErrorCode.SQL_SUCH_APARTMENT_DOES_NOT_EXIST, trace_id)

        session.commit()

        return apartment_data

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_UPDATING_ENTRY, error) # Assuming error code
        raise APIError(ErrorCode.SQL_ERROR_UPDATING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()

def update_tenancy(
                    id_tenancy: int,
                    id_apartment: int,
                    id_tenant_personal_data: int,
                    id_rent_data: int,
                    move_in_date: str,
                    move_out_date: str,
                    deposit: float,
                    registered_address: str,
                    comment: str) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_tenancy not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_UPDATING_ENTRY)

        session = Session()

        # filter by personal ID
        query = session.query(Tenancy).filter(
            Tenancy.id_tenancy == id_tenancy
        )

        # try to get the person to update
        tenancy = query.one_or_none()

        if tenancy is None:
            raise APIError(ErrorCode.SQL_SUCH_TENANCY_DOES_NOT_EXIST) # Assuming error code

        # update person with new data
        if id_apartment not in (None, ""):
            tenancy.id_apartment = id_apartment

        if id_tenant_personal_data not in (None, ""):
            tenancy.id_tenant_personal_data = id_tenant_personal_data

        if id_rent_data not in (None, ""):
            tenancy.id_rent_data = id_rent_data

        if move_in_date not in (None, ""):
            tenancy.move_in_date = move_in_date

        if move_out_date not in (None, ""):
            tenancy.move_out_date = move_out_date

        if deposit not in (None, ""):
            tenancy.deposit = deposit

        if registered_address not in (None, ""):
            tenancy.registered_address = registered_address

        if comment not in (None, ""):
            tenancy.comment = comment

        if tenancy:
            # save the data of the person, that will be deleted in the next step
            tenancy_data = tenancy.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_TENANCY_DOES_NOT_EXIST)
            raise APIError(ErrorCode.SQL_SUCH_TENANCY_DOES_NOT_EXIST, trace_id)

        session.commit()

        return tenancy_data

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_UPDATING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_UPDATING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()

def update_contract(
                    id_rent_data: int,
                    net_rent: float,
                    utility_costs: float,
                    vat: float,
                    garage: float,
                    parking_spot: float,
                    comment: str) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_rent_data not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_UPDATING_ENTRY)

        session = Session()

        # filter by personal ID
        query = session.query(Contract).filter(
            Contract.id_rent_data == id_rent_data
        )

        # try to get the person to update
        contract = query.one_or_none()

        if contract is None:
            raise APIError(ErrorCode.SQL_SUCH_CONTRACT_DOES_NOT_EXIST) # Assuming error code

        # update person with new data
        if net_rent not in (None, ""):
            contract.net_rent = net_rent

        if utility_costs not in (None, ""):
            contract.utility_costs = utility_costs

        if vat not in (None, ""):
            contract.vat = vat

        if garage not in (None, ""):
            contract.garage = garage

        if parking_spot not in (None, ""):
            contract.parking_spot = parking_spot

        if comment not in (None, ""):
            contract.comment = comment

        if contract:
            # save the data of the person, that will be deleted in the next step
            contract_data = contract.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_CONTRACT_DOES_NOT_EXIST)
            raise APIError(ErrorCode.SQL_SUCH_CONTRACT_DOES_NOT_EXIST, trace_id)

        session.commit()

        return contract_data

    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_UPDATING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_UPDATING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()