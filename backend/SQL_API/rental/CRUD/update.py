from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Session

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
        session.close()