from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Session, Apartment, Tenancy, Contract

def delete_person(*, # make order of arguments not important, as the LLM can mix it
                    first_name: str,
                    last_name: str,
                    id_personal_data: int) -> dict:
    """
    Deletes a person's record from the database based on provided identification
    or name details. Either a personal ID or both first and last names must be
    provided as input for the deletion to proceed. If neither parameters nor valid
    data are present, an error is raised. The operation involves database query
    execution and commits the changes if successful. In case of errors during
    execution, an appropriate rollback is performed.

    :param first_name: First name of the person whose record is to be deleted
        if the ID is not given.
    :type first_name: str
    :param last_name: Last name of the person whose record is to be deleted
        if the ID is not given.
    :type last_name: str
    :param id_personal_data: Unique identifier (personal data ID) of the person
        whose record is being deleted.
    :type id_personal_data: str
    :return: A dictionary containing the operation result (True) and the
        details of the person whose record was deleted, including `person_id`,
        `first_name`, and `last_name`.
    :rtype: dict
    :raises APIError: If neither the ID nor both first and last names are
        provided as input, or if an error occurs during the database operation.
    """
    session = None

    try:
        # Parameter validation rules
        id_given = id_personal_data not in (None, "")
        name_given = first_name not in (None, "") and last_name not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given and not name_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_DELETING_ENTRY)

        session = Session()

        # filter by personal ID
        if id_given:
            query = session.query(PersonalData).filter(
                PersonalData.id_personal_data == id_personal_data
            )
        else: # filter by first name and last name
            query = session.query(PersonalData).filter(
                PersonalData.first_name == first_name,
                PersonalData.last_name == last_name
            )

        # try to get the person to delete
        person = query.one_or_none()

        if person:
            # save the data of the person, that will be deleted in the next step
            person_data = person.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_PERSON_DOES_NOT_EXIST)
            raise APIError(ErrorCode.SQL_SUCH_PERSON_DOES_NOT_EXIST, trace_id)

        query.delete()
        session.commit()

        return person_data

    except APIError:
        if session:
            session.rollback()
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_DELETING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_DELETING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()

def delete_apartment(*,
                     address: str,
                     id_apartment: int) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_apartment not in (None, "")
        address_given = address not in (None, "")

        # If just one of both (first name and last name) are provided, and the ID is not provided
        if not id_given and not address_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_DELETING_ENTRY)

        session = Session()

        # filter by personal ID
        if id_given:
            query = session.query(Apartment).filter(
                Apartment.id_apartment == id_apartment
            )
        else: # filter by first name and last name
            query = session.query(Apartment).filter(
                Apartment.address == address
            )

        # try to get the person to delete
        apartment = query.one_or_none()

        if apartment:
            # save the data of the person, that will be deleted in the next step
            apartment_data = apartment.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_APARTMENT_DOES_NOT_EXIST) # Assuming error code
            raise APIError(ErrorCode.SQL_SUCH_APARTMENT_DOES_NOT_EXIST, trace_id)

        query.delete()
        session.commit()

        return apartment_data

    except APIError:
        if session:
            session.rollback()
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_DELETING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_DELETING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()

def delete_tenancy(*,
                   id_tenancy: int,
                   id_apartment: int,
                   id_tenant_personal_data: int) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_tenancy not in (None, "")
        apartment_given = id_apartment not in (None, "")
        tenant_given = id_tenant_personal_data not in (None, "")

        if not id_given and not apartment_given and not tenant_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_DELETING_ENTRY)

        session = Session()

        if id_given:
            query = session.query(Tenancy).filter(
                Tenancy.id_tenancy == id_tenancy
            )
        elif apartment_given:
            query = session.query(Tenancy).filter(
                Tenancy.id_apartment == id_apartment
            )
        else:
            query = session.query(Tenancy).filter(
                Tenancy.id_tenant_personal_data == id_tenant_personal_data
            )

        # try to get the person to delete
        tenancy = query.one_or_none()

        if tenancy:
            # save the data of the person, that will be deleted in the next step
            tenancy_data = tenancy.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_TENANCY_DOES_NOT_EXIST) # Assuming error code
            raise APIError(ErrorCode.SQL_SUCH_TENANCY_DOES_NOT_EXIST, trace_id)

        query.delete()
        session.commit()

        return tenancy_data

    except APIError:
        if session:
            session.rollback()
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_DELETING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_DELETING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()

def delete_contract(*,
                    id_contract: int) -> dict:
    session = None

    try:
        # Parameter validation rules
        id_given = id_contract not in (None, "")

        if not id_given:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_DELETING_ENTRY)

        session = Session()

        query = session.query(Contract).filter(
            Contract.id_contract == id_contract
        )

        # try to get the person to delete
        contract = query.one_or_none()

        if contract:
            # save the data of the person, that will be deleted in the next step
            contract_data = contract.to_dict()
        else:
            trace_id = log_error(ErrorCode.SQL_SUCH_CONTRACT_DOES_NOT_EXIST) # Assuming error code
            raise APIError(ErrorCode.SQL_SUCH_CONTRACT_DOES_NOT_EXIST, trace_id)

        query.delete()
        session.commit()

        return contract_data

    except APIError:
        if session:
            session.rollback()
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_DELETING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_DELETING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()