from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Session

def delete_person(first_name: str,
                    last_name: str,
                    id_personal_data: int) -> dict:
    """
    Deletes a person's record from the database based on provided identification
    or name details. Either a personal ID or both first and last names must be
    provided as input for the deletion to proceed. If neither parameters nor valid
    data are present, an error is raised. The operation involves database query
    execution and commits the changes if successful. In case of errors during
    execution, an appropriate rollback is performed.

    :param first_name: First name of the person whose record is to be deleted,
        if the ID is not given.
    :type first_name: str
    :param last_name: Last name of the person whose record is to be deleted,
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

        query.delete()
        session.commit()

        return {"result": True,
                "person_id": id_personal_data,
                "first_name": first_name,
                "last_name": last_name}

    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_DELETING_ENTRY, error)
        raise APIError(ErrorCode.SQL_ERROR_DELETING_ENTRY, trace_id) from error
    finally:
        if session:
            session.close()