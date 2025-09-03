import traceback

from ApartmentManager.backend.SQL_API.orm_models import Apartment, PersonalData, Session

session = Session()

try:
    apartment_EG_2 = Apartment(
        id_apartment=7,
        area = 100,
        address = "Müllerstr.5, Berlin",
        price_per_square_meter = 16,
        utility_billing_provider_id = 17
    )
    session.add(apartment_EG_2)

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
    """

    session.commit()

except Exception as error:
    print(f"Error reading database: {error}")
    traceback.print_exc()
    session.rollback()
finally:
    session.close()