import json
import os
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from requests import RequestException

from ApartmentManager.backend.AI_API.general.conversation_delete_entity import delete_entity_from_db
from ApartmentManager.backend.AI_API.general.conversation_state import ConversationState, CrudState
from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.conversation_create_entity import create_entity_in_db
from ApartmentManager.backend.AI_API.general.conversation_crud_check import ai_set_conversation_state
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.AI_API.general.conversation_show_entity import show_entity_from_db


class ConversationClient:
    """
    Initializes an LLM client and offers methods to open conversation with it.
    """
    def __init__(self, model_name):
        self.llm_client = None
        self.model_name = model_name
        self.crud_intent_data = None
        self.conversation_state = ConversationState()
        self.system_prompt = prompting.GET_FUNCTION_CALL_PROMPT
        self.do_once = True

        # Specify the model to use
        load_dotenv()
        some_gemini_model = os.getenv("GEMINI_MODEL") # for example, gemini-2.5-flash

        if self.model_name == some_gemini_model:
            self.llm_client = GeminiClient(some_gemini_model)
            print("Gemini will answer your question.")
        elif self.model_name == "Groq":
            #self.llm_client = GroqClient(active_model_name)
            print("Groq will answer your question.")

    def reset_settings(self):
        self.conversation_state.reset()
        self.do_once = True
        self.system_prompt = prompting.GET_FUNCTION_CALL_PROMPT

    def get_llm_answer(self, user_question: str) -> dict:
        """
        Get a response of the LLM model on the user's question.
        :param user_question: User question.
        :return: Envelope with the type: "text" | "data"
        """
        result = None

        if self.conversation_state.is_none:
            # Runs the CRUD check over the user question
            # and depending on the CRUD operation in it, sets the state
            self.crud_intent_data = ai_set_conversation_state(self, user_question)

        try:
            # Do action depending on CRUD operation using match/case
            match self.conversation_state.state:
                case CrudState.CREATE:
                    result = create_entity_in_db(self, user_question)

                case CrudState.DELETE:
                    result = delete_entity_from_db(self, user_question)

                case CrudState.UPDATE:
                    if result:
                        self.reset_settings()
                    trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
                    raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

                case CrudState.SHOW:
                    result = show_entity_from_db(self, user_question)
                    if result:
                        self.reset_settings()

                case CrudState.NONE:
                    system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2, ensure_ascii=False)
                    result = self.llm_client.answer_general_questions(user_question, system_prompt)

            if not result:
                trace_id = log_error(ErrorCode.LLM_ERROR_EMPTY_ANSWER)
                raise APIError(ErrorCode.LLM_ERROR_EMPTY_ANSWER, trace_id)
            return result

        except APIError:
            self.reset_settings()
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            self.reset_settings()
            raise
        except RequestException:
            self.reset_settings()
            raise
        except Exception as error:
            self.reset_settings()
            trace_id = log_error(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, exception=error)
            raise APIError(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, trace_id) from error