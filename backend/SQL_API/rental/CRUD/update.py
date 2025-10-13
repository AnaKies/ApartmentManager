import traceback

from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Session

session = Session()

try:
    person_to_update = (session.query(PersonalData)
                        .filter(PersonalData.last_name == "Schmid")
                        .one())

    person_to_update.last_name = "Sauter"
    person_to_update.email = "maria.sauter@g,ail.com"

    session.commit()

except Exception as error:
    print(f"Error reading database: {error}")
    traceback.print_exc()
    session.rollback()
finally:
    session.close()