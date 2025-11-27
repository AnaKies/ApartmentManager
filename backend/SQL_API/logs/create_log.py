import traceback

from ApartmentManager.backend.SQL_API.logs.logs_orm_models import Log, Session

def create_new_log_entry(llm_model: str,
                         user_question: str,
                         request_type: str,
                         backend_response: str,
                         llm_answer: str,
                         system_prompt_name: str):

    # create the Session only for one log
    session = Session()

    # Put arguments to dict to do the input check in the next step
    args = {
        "llm_model": llm_model,
        "user_question": user_question,
        "request_type": request_type,
        "backend_response": backend_response,
        "llm_answer": llm_answer,
        "system_prompt_name": system_prompt_name
    }
    try:
        # Input check
        for name, value in args.items():
            if not isinstance(value, str):
                raise TypeError(f"Argument '{name}' must be of type str, got {type(value).__name__} instead.")

        log_entry = Log(ai_model=llm_model,
                        user_question=user_question,
                        request_type=request_type,
                        back_end_response=backend_response,
                        ai_answer=llm_answer,
                        system_prompt_name=system_prompt_name)
        session.add(log_entry)
        session.commit()

    except Exception as error:
        print(f"Error reading database: {error}")
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()