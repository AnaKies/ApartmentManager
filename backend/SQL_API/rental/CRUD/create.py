from ApartmentManager.backend.SQL_API.rental.rental_orm_models import Apartment, Session, PersonalData
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error

def create_person(first_name: str,
                    last_name: str,
                    bank_data: str,
                    phone_number: str,
                    email: str,
                    comment: str) -> dict:
    """
    Creates a new entry for a person in the database. The function gathers
    information about a person, validates the essential parameters, and
    stores the data in the database. If successful, it returns a dictionary
    containing a success indicator and stored attributes like `person_id`,
    `first_name`, and `last_name`.

    :param first_name: The first name of the person
    :param last_name: The last name of the person
    :param bank_data: Bank account information of the person
    :param phone_number: The contact phone number of the person
    :param email: Email address of the person
    :param comment: Additional comments or contextual information regarding the person

    :return: A dictionary containing the operation result, the ID of the created
             person (if successful), `first_name`, and `last_name`.

    :raises APIError: If essential parameters like `first_name` or `last_name` are
                      invalid, or if an error occurs during database interaction.

    """
    session = None
    try:
        session = Session()

        person = PersonalData(
            first_name = first_name,
            last_name = last_name,
            bank_data = bank_data,
            phone_number = phone_number,
            email = email,
            comment = comment)

        required_params = first_name not in (None, "") and last_name not in (None, "")

        if not required_params:
            raise APIError(ErrorCode.SQL_PARAMETER_ERROR_CREATING_NEW_PERSON)

        session.add(person)
        session.commit()

        return {"result": True,
                "person_id": getattr(person, "id_personal_data", None),
                "first_name": first_name,
                "last_name": last_name}
    except APIError:
        raise
    except Exception as error:
        if session:
            session.rollback()
        trace_id = log_error(ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON, error)
        raise APIError(ErrorCode.SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON, trace_id) from error
    finally:
        if session:
            session.close()


    """
    personal_data = [
        PersonalData(first_name="Maria", last_name="Schmid", bank_data="DE3567", phone_number="+495438", email="schmid@mail.de", comment="Betreuung"),
        PersonalData(first_name="Lukas", last_name="Müller", bank_data="DE1234", phone_number="+491234567", email="lukas.mueller@mail.de", comment="Neue Mieter"),
        PersonalData(first_name="Anna", last_name="Weber", bank_data="DE5678", phone_number="+492345678", email="anna.weber@mail.de", comment="Zahlung ausstehend"),
        PersonalData(first_name="Jonas", last_name="Schneider", bank_data="DE9101", phone_number="+493456789", email="jonas.schneider@mail.de", comment="Schlüssel abgegeben"),
        PersonalData(first_name="Sophie", last_name="Fischer", bank_data="DE1121", phone_number="+494567890", email="sophie.fischer@mail.de", comment="Vertragsverlängerung"),
        PersonalData(first_name="Max", last_name="Becker", bank_data="DE3141", phone_number="+495678901", email="max.becker@mail.de", comment="Einzug geplant")
    ]
    session.add_all(personal_data)


res = create_person(first_name="Olga" ,
                    last_name="Ivanova",
                    bank_data="RU34567",
                    phone_number="+7235890",
                    email="olga.ivanova@mail.ru",
                    comment="new tenant from oktober")
    """