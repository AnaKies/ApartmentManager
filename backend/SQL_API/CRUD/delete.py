import traceback
from ApartmentManager.backend.SQL_API.orm_models import PersonalData, Session

session = Session()

try:
    (session.query(PersonalData)
     .filter(PersonalData.last_name == "Becker")
     .delete())
    session.commit()

except Exception as error:
    print(f"Error reading database: {error}")
    traceback.print_exc()
    session.rollback()
finally:
    session.close()