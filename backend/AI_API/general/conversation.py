import json
import os
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from requests import RequestException
from ApartmentManager.backend.AI_API.general.conversation_state import ConversationState, CrudState
from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.create_entity import create_entity_in_db
from ApartmentManager.backend.AI_API.general.crud_check import ai_set_conversation_state
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person
from ApartmentManager.backend.AI_API.general.error_texts import APIError
from ApartmentManager.backend.AI_API.general.api_data_type import build_text_answer, build_data_answer
from ApartmentManager.backend.AI_API.general.logger import log_error


class ConversationClient:
    """
    Initializes an LLM client and offers methods to open conversation with it.
    """
    def __init__(self, model_name):
        self.llm_client = None
        self.model_name = model_name
        self.crud_intent_data = None
        self.conversation_state = ConversationState()
        self.system_prompt = None

        # Specify the model to use
        load_dotenv()
        some_gemini_model = os.getenv("GEMINI_MODEL") # for example, gemini-2.5-flash

        if self.model_name == some_gemini_model:
            self.llm_client = GeminiClient(some_gemini_model)
            print("Gemini will answer your question.")
        elif self.model_name == "Groq":
            #self.llm_client = GroqClient(active_model_name)
            print("Groq will answer your question.")

    def get_llm_answer(self, user_question: str) -> dict:
        """
        Get a response of the LLM model on the user's question.
        :param user_question: User question.
        :return: Envelope with the type: "text" | "data"
        """
        result = None

        # Runs the CRUD check over the user question
        # and depending on the CRUD operation in it, sets the state
        self.crud_intent_data = ai_set_conversation_state(self, user_question)

        try:
            # TODO change to switch/case
            # STEP 2: do action depending on CRUD operation
            if self.conversation_state.is_create:
                result = create_entity_in_db(self, user_question)

            elif self.conversation_state.is_delete:
                # Generate prompt for DELETE operation
                if result:
                    self.conversation_state.reset()
                trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
                raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

            elif self.conversation_state.is_update:
                # Generate prompt for UPDATE operation
                if result:
                    self.conversation_state.reset()
                trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
                raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

            elif self.conversation_state.is_show:
                sql_answer = None

                # STEP 1: Data preparation
                system_prompt = json.dumps(prompting.SHOW_TYPE_CLASSIFIER_PROMPT, indent=2, ensure_ascii=False)
                # LLM checks if the user provides the data type to show
                prepare_data_to_show = self.llm_client.process_show_request(user_question, system_prompt)

                # STEP 2: Action of the back-end
                missing_request = None
                # Analyzes what type of data should be shown and does the SQL calls
                if ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("checked"):
                    data_type_to_show = ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("type")
                    if data_type_to_show == "person":
                        sql_answer = get_persons()
                    elif data_type_to_show == "apartment":
                        sql_answer = get_apartments()
                    elif data_type_to_show == "tenancy":
                        sql_answer = get_tenancies()
                    elif data_type_to_show == "contract":
                        sql_answer = get_contract()
                else:
                    # Return the request that did not fit to the types above
                    missing_request = ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("message")

                if sql_answer :
                    payload = [element.to_dict() for element in sql_answer]
                    self.conversation_state.reset()

                    result = build_data_answer(payload=payload or {},
                                               payload_comment=missing_request or "Data updated", # this text shows the user reaction when the data is shown
                                               model=self.model_name,
                                               answer_source="backend")

                else:
                    trace_id = log_error(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY)
                    raise APIError(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY, trace_id)

            elif  self.conversation_state.is_none:
                # New system prompt providing a structured output for collected data
                system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2, ensure_ascii=False)
                # State machine for general questions
                result = self.llm_client.answer_general_questions(user_question, system_prompt)

            if not result:
                trace_id = log_error(ErrorCode.LLM_ERROR_EMPTY_ANSWER)
                raise APIError(ErrorCode.LLM_ERROR_EMPTY_ANSWER, trace_id)
            return result

        except APIError:
            self.conversation_state.reset()
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            self.conversation_state.reset()
            raise
        except RequestException:
            self.conversation_state.reset()
            raise
        except Exception as error:
            self.conversation_state.reset()
            trace_id = log_error(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, exception=error)
            raise APIError(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, trace_id) from error