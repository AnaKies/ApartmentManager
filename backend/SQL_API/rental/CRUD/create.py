from ApartmentManager.backend.SQL_API.rental.rental_orm_models import Apartment, Session, PersonalData


def create_person(first_name: str,
                    last_name: str,
                    bank_data: str,
                    phone_number: str,
                    email: str,
                    comment: str) -> dict:
    """
    Adds a person to the database. Answer contains also the ID that the databank assigned.
    :param first_name:
    :param last_name:
    :param bank_data:
    :param phone_number:
    :param email:
    :param comment:
    :return: Dictionary {"result": "OK", "id_personal_data": ...} or {"result": "error", "message": ...}
    """
    session = Session()
    try:
        person = PersonalData(
            first_name = first_name,
            last_name = last_name,
            bank_data = bank_data,
            phone_number = phone_number,
            email = email,
            comment = comment)

        session.add(person)
        session.commit()
        return {"result": True, "message": getattr(person, "id_personal_data", None)}
    except Exception as error:
        print(f"Error reading database: ", repr(error))
        session.rollback()
        return {"result": False, "message": repr(error)}
    finally:
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