import json
from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.errors_backend import ErrorCode
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person

class ConversationState:
    show_state = False
    update_state = False
    delete_state = False
    create_state = False
    default_state = False

class LlmClient:
    """
    Initializes an LLM client and offers methods to open conversation with it.
    """
    def __init__(self, model_choice):
        self.llm_client = None
        self.model = model_choice

        if self.model == "Gemini":
            self.llm_client = GeminiClient()
            print("Gemini will answer your question.")
        elif self.model == "Groq":
            #self.llm_client = GroqClient()
            print("Groq will answer your question.")

    def get_llm_answer(self, user_question: str) -> dict:
        """
        Get response of the LLM model on user's question.
        :param user_question: User question.
        :return: Envelope with type: "text" | "data"
        """
        crud_intent = None
        result = None

        try:
            if (not ConversationState.show_state or
                    not ConversationState.create_state or
                    not ConversationState.update_state or
                    not ConversationState.delete_state):
                # STEP 1: LLM checks if user asks for one of CRUD operations
                crud_intent = self.llm_client.get_crud_in_user_question(user_question)

            # actualize the state of the state machine
            if ((crud_intent or {}).get("create") or {}).get("value"):
                ConversationState.create_state = True
            elif ((crud_intent or {}).get("update") or {}).get("value"):
                ConversationState.update_state = True
            elif ((crud_intent or {}).get("delete") or {}).get("value"):
                ConversationState.delete_state = True
            elif ((crud_intent or {}).get("show") or {}).get("value"):
                ConversationState.show_state = True
            else:
                ConversationState.default_state = True

        except Exception as error:
            print(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT + " :",repr(error))
            return {
                "type": "error",
                "result": {
                    "message": crud_intent
                },
                "meta": {
                    "model": self.model
                },
                "error": {"code": ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT +" :" + repr(error)}
            }

        try:
            # STEP 2: do action depending on CRUD operation
            if ConversationState.create_state:
                # Generate prompt for CREATE operation
                prompt_for_entity_creation = self.llm_client.generate_prompt_for_create_entity(crud_intent)
                system_prompt = json.dumps(prompt_for_entity_creation, indent=2, ensure_ascii=False)
                response = self.llm_client.process_create_request(user_question, system_prompt)

                result = (response.get("result" or {}).get("payload") or {}).get("message")

                if response.get("ready_to_post"):
                    # Extract fields from dictionary and give them the function
                    args = response.get("payload")
                    parsed_args= json.loads(args)
                    result = create_person(**parsed_args)

                    ConversationState.create_state = False

                result = {
                    "type": "text",
                    "result": {
                        "message": result
                    },
                    "meta": {
                        "model": self.model
                    }
                }

            elif ConversationState.delete_state:
                # Generate prompt for DELETE operation
                if result:
                    ConversationState.delete_state = False

            elif ConversationState.update_state:
                # Generate prompt for UPDATE operation
                if result:
                    ConversationState.update_state = False

            elif ConversationState.show_state:
                sql_answer = None
                payload = None

                # Default prompt allows possible function call as read-only operation (GET)
                system_prompt = json.dumps(prompting.SHOW_TYPE_CLASSIFIER_PROMPT, indent=2, ensure_ascii=False)
                # LLM checks if the data type to show is provided by the user
                prepare_data_to_show = self.llm_client.process_show_request(user_question, system_prompt)

                # Analyzes what type of data should be shown and show it
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
                    payload = ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("message")

                if sql_answer :
                    payload = [element.to_dict() for element in sql_answer]
                    ConversationState.show_state = False

                result = {
                    "type": "data",
                    "result": {
                        "payload": payload
                    },
                    "meta": {
                        "model": self.model
                    }
                }

            elif ConversationState.default_state:
                # Default prompt allows possible function call as read-only operation (GET)
                system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2, ensure_ascii=False)
                # State machine for general questions
                result = self.llm_client.answer_general_questions(user_question, system_prompt)

        except Exception as error:
            print(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION + " :",repr(error))
            return {
                "type": "error",
                "result": {
                    "message": crud_intent
                },
                "meta": {
                    "model": self.model
                },
                "error": {"code": ErrorCode.ERROR_PERFORMING_CRUD_OPERATION +" :" + repr(error)}
            }

        return result
