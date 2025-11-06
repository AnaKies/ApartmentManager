import json
from logging import exception

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person
from ApartmentManager.backend.AI_API.general.error_texts import APIError
from ApartmentManager.backend.AI_API.general.api_data_type import build_text_answer, build_data_answer
from ApartmentManager.backend.AI_API.general.logger import log_error, log_warning

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
        self.crud_intent = None

        if self.model == "Gemini":
            self.llm_client = GeminiClient()
            print("Gemini will answer your question.")
        elif self.model == "Groq":
            #self.llm_client = GroqClient()
            print("Groq will answer your question.")

    def get_llm_answer(self, user_question: str) -> dict:
        """
        Get a response of the LLM model on the user's question.
        :param user_question: User question.
        :return: Envelope with the type: "text" | "data"
        """
        result = None
        ran_crud_check = False

        # TODO CRUD Check: check for a shorter way with default state only
        try:
            # If one of the CRUD states is active, do not perform the CRUD check
            # Reason: a single CRUD state can consist of multiple conversation-cycles/iterations
            # At the start even the default state is False -> the CRUD check is always done at the start

            # Check no active CRUD state
            is_any_active = any([
                ConversationState.show_state,
                ConversationState.create_state,
                ConversationState.update_state,
                ConversationState.delete_state
            ])
            if not is_any_active:
                # STEP 1: LLM checks if a user asks for one of CRUD operations
                self.crud_intent = self.llm_client.get_crud_in_user_question(user_question)
                ran_crud_check = True

            # actualize the state of the state machine
            if ran_crud_check:
                if ((self.crud_intent or {}).get("create") or {}).get("value"):
                    ConversationState.create_state = True
                    ConversationState.update_state = False
                    ConversationState.delete_state = False
                    ConversationState.show_state = False
                    ConversationState.default_state = False
                elif ((self.crud_intent or {}).get("update") or {}).get("value"):
                    ConversationState.create_state = False
                    ConversationState.update_state = True
                    ConversationState.delete_state = False
                    ConversationState.show_state = False
                    ConversationState.default_state = False
                elif ((self.crud_intent or {}).get("delete") or {}).get("value"):
                    ConversationState.create_state = False
                    ConversationState.update_state = False
                    ConversationState.delete_state = True
                    ConversationState.show_state = False
                    ConversationState.default_state = False
                elif ((self.crud_intent or {}).get("show") or {}).get("value"):
                    ConversationState.create_state = False
                    ConversationState.update_state = False
                    ConversationState.delete_state = False
                    ConversationState.show_state = True
                    ConversationState.default_state = False
                else:
                    # No explicit CRUD intent detected at the start of a conversation => default
                    ConversationState.create_state = False
                    ConversationState.update_state = False
                    ConversationState.delete_state = False
                    ConversationState.show_state = False
                    ConversationState.default_state = True
            # NOTE: if we did NOT run a CRUD check (multi-turn within an active state),
            #       we DO NOT touch the existing ConversationState flags here.

        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT, error)
            raise APIError(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT, trace_id)

        try:
            # TODO change to switch/case
            # STEP 2: do action depending on CRUD operation
            if ConversationState.create_state:
                # STEP 1: Provide extended system prompt with injected data
                # Generate new prompt for CREATE operation
                prompt_for_entity_creation = self.llm_client.generate_prompt_for_create_entity(self.crud_intent)
                system_prompt = json.dumps(prompt_for_entity_creation, indent=2, ensure_ascii=False)

                # STEP 2: Do the LLM call to collect the data for creating an entry
                # and get the user's confirmation for them.
                # Multiple conversation cycles logic.
                response = self.llm_client.process_create_request(user_question, system_prompt)

                # First, open the envelope of the structured output service
                result_output = (response or {}).get("result")
                payload_struct_output = (result_output or {}).get("payload")
                llm_comment_to_payload = (payload_struct_output or {}).get("comment")

                # STEP 3: Backend calls the SQL layer to create a new entry
                if (payload_struct_output or {}).get("ready_to_post"):
                    # Extract data fields to give them the function
                    args = (payload_struct_output or {}).get("data")
                    parsed_args= json.loads(args)

                    # Back-end calls directly the method to add a person to SQL databank
                    creation_action_data = create_person(**parsed_args)

                    # STEP 4:
                    if creation_action_data:
                        creation_action_flag = (creation_action_data or {}).get("result")

                        if creation_action_flag:
                            id_person = (creation_action_data or {}).get("person_id")
                            result = build_text_answer(message=f"Person with ID {id_person} was created successfully.",
                                                        model=self.model,
                                                        answer_source="backend")
                            create_new_log_entry(
                                llm_model=self.model,
                                user_question=user_question or "---",
                                request_type="person creation request",
                                backend_response=str(result),
                                llm_answer="---"
                            )

                            ConversationState.create_state = False
                        else: # Creation flag is not active
                            trace_id = log_error(ErrorCode.SQL_ERROR_CREATING_NEW_PERSON, exception=None)
                            raise APIError(ErrorCode.SQL_ERROR_CREATING_NEW_PERSON, trace_id)

                # STEP 5: Wait for new conversation cycle until user provided all data
                # and LLM set the flag redy_to_post.
                # Return the actual comment of the LLM, which should ask for missing data
                else:
                    ConversationState.create_state = True  # keep collecting until confirmation
                    result = build_text_answer(message=llm_comment_to_payload,
                                                   model=self.model,
                                                   answer_source="llm")

            elif ConversationState.delete_state:
                # Generate prompt for DELETE operation
                if result:
                    ConversationState.delete_state = False
                raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED)

            elif ConversationState.update_state:
                # Generate prompt for UPDATE operation
                if result:
                    ConversationState.update_state = False
                raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED)

            elif ConversationState.show_state:
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
                    ConversationState.show_state = False

                    result = build_data_answer(payload=payload or {},
                                                payload_comment=missing_request or "-",
                                                model=self.model,
                                                answer_source="llm")

                else:
                    trace_id = log_error(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY)
                    raise APIError(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY, trace_id)

            elif ConversationState.default_state:
                # New system prompt providing a structured output for collected data
                system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2, ensure_ascii=False)
                # State machine for general questions
                result = self.llm_client.answer_general_questions(user_question, system_prompt)
        except APIError as api_error:
            log_error(exception=api_error)
            raise api_error
        except Exception as error:
            trace_id = log_error(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, exception=error)
            raise APIError(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, trace_id)

        if not result:
            trace_id = log_error(ErrorCode.LLM_ERROR_EMPTY_ANSWER)
            raise APIError(ErrorCode.LLM_ERROR_EMPTY_ANSWER, trace_id)
        return result
