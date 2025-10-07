import traceback

from ApartmentManager.backend.SQL_API.logs.logs_orm_models import Log, Session

session = Session()

def create_new_log_entry(ai_model: str, user_question: str, backend_response: str, ai_answer: str):
    try:
        log_entry = Log(ai_model=ai_model,
                        user_question=user_question,
                        back_end_response=backend_response,
                        ai_answer=ai_answer)
        session.add(log_entry)

        session.commit()

    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()