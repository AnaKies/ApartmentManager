import json
import os
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from requests import RequestException
from ApartmentManager.backend.AI_API.general.conversation_state import ConversationState, CrudState
from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
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

                # Generate the system prompt only once over the conversation iterations
                if self.conversation_state.do_once:
                    self.conversation_state.do_once = False

                    # STEP 1: Provide extended system prompt with injected data
                    # Generate new prompt for CREATE operation
                    self.system_prompt = self.llm_client.generate_prompt_to_create_entity(self.crud_intent_data)

                # STEP 2: Do the LLM call to collect the additional data for creating an entry
                # and get the user's confirmation for them.
                # Multiple conversation cycles logic.
                if self.system_prompt:
                    response = self.llm_client.process_create_request(user_question, self.system_prompt)
                else:
                    trace_id = log_error(ErrorCode.NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_CREATE_OPERATION)
                    raise APIError(ErrorCode.NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_CREATE_OPERATION, trace_id)

                # First, open the envelope of the structured output service
                if response:
                    result_output = (response or {}).get("result")
                    payload_struct_output = (result_output or {}).get("payload")
                    llm_comment_to_payload = (payload_struct_output or {}).get("comment")
                else:
                    trace_id = log_error(ErrorCode.NO_ACTIVATION_OF_RESPONSE_FOR_CREATE_OPERATION)
                    raise APIError(ErrorCode.NO_ACTIVATION_OF_RESPONSE_FOR_CREATE_OPERATION, trace_id)

                # STEP 3: Backend calls the SQL layer to create a new entry
                if (payload_struct_output or {}).get("ready_to_post"):
                    # Extract data fields to give them the function
                    args = (payload_struct_output or {}).get("data")
                    parsed_args= json.loads(args)

                    # Back-end calls directly the method to add an entity to SQL databank
                    creation_action_data = create_person(**parsed_args)

                    # STEP 4: evaluate new entity creation
                    if creation_action_data:
                        creation_action_flag = (creation_action_data or {}).get("result")

                        if creation_action_flag:
                            id_person = (creation_action_data or {}).get("person_id")
                            result = build_text_answer(message=f"Person with ID {id_person} was created successfully.",
                                                       model=self.model_name,
                                                       answer_source="backend")
                            create_new_log_entry(
                                llm_model=self.model_name,
                                user_question=user_question or "---",
                                request_type="person creation request",
                                backend_response=str(result),
                                llm_answer="---"
                            )
                            # resets also the do_once flag
                            self.conversation_state.reset()

                # STEP 5: Wait for new conversation cycle until user provided all data
                # and LLM set the flag ready_to_post.
                # Return the actual comment of the LLM, which should ask for missing data
                else:
                     # keep collecting data for creating new entity
                     # until the user confirmed the collected data
                    result = build_text_answer(message=llm_comment_to_payload,
                                               model=self.model_name,
                                               answer_source="llm")

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