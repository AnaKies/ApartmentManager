from ApartmentManager.backend.AI_API.general.json_serialisation import dumps_for_llm_prompt
import os
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from requests import RequestException
from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general.prompting import Prompt
from ApartmentManager.backend.AI_API.general.conversation_write_actions import write_action_to_entity
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import EnvelopeApi
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.AI_API.general.conversation_read_action import read_action_to_entity
import uuid

class ConversationClient:
    """
    Initializes an LLM and offers methods to open conversation with it.
    """
    def __init__(self, model_name):
        self.llm_client = None
        self.model_name = model_name
        self.result = None
        self.system_prompt = Prompt.GET_FUNCTION_CALL.value # separate with the name because of prompt injection
        self.system_prompt_name = Prompt.GET_FUNCTION_CALL.name
        self.user_question = None
        self.crud_intent_answer = None
        self.operation_id = None

        # Specify the model to use
        load_dotenv()
        some_gemini_model = os.getenv("GEMINI_MODEL") # for example, gemini-2.5-flash

        if self.model_name == some_gemini_model:
            self.llm_client = GeminiClient(some_gemini_model)
            print("Gemini will answer your question.")
        elif self.model_name == "Groq":
            #self.llm_client = GroqClient(active_model_name)
            print("Groq will answer your question.")

    def extract_operation_ids_from_crud_answer(self) -> dict:
        """
        Extracts operation_ids from the last CRUD intent answer.
        Returns dict suitable for interrupted_operations injection.
        Structure: {operation_type: {"operation_id": str, "type": str}}
        Only includes operations where value=False and operation_id is not empty.
        """
        if not self.crud_intent_answer:
            return {}

        interrupted_ops = {}

        # Check each operation type (show is excluded - stateless)
        for crud_operation_type in ["create", "update", "delete"]:
            operation = getattr(self.crud_intent_answer, crud_operation_type)
            # If the operation is not active (value=False) but has operation_id, it's interrupted
            if not operation.value and operation.operation_id:
                interrupted_ops[crud_operation_type] = {
                    "operation_id": operation.operation_id,
                    "type": operation.type
                }

        return interrupted_ops


    def get_llm_answer(self, user_question: str) -> EnvelopeApi:
        """
        Get a response of the LLM model on the user's question.
        :param user_question: User question.
        :return: Envelope with the type: "text" | "data"
        """
        self.user_question = user_question

        # is cyclically set to False by the cycled LLM call.
        # if not reset means a READ operation without extra cycles for collecting information
        cycle_is_ready = True

        try:
            # Run main head assistant
            # LLM checks if a user asks for one of CRUD operations
            self.crud_intent_answer = self.llm_client.crud_intent_assistant.get_crud_llm_response(self)

            # Write operations (cyclic behavior)
            if (self.crud_intent_answer.create.value or
                self.crud_intent_answer.update.value or
                self.crud_intent_answer.delete.value):

                # Replace "NEW" markers with actual UUIDs (only for create/update/delete)
                for op_type in ["create", "update", "delete"]:
                    operation = getattr(self.crud_intent_answer, op_type)
                    if operation.value and operation.operation_id == "NEW":
                        operation.operation_id = str(uuid.uuid4())[:8]

                # Sync self.operation_id with the active operation's ID
                # This ensures we switch IDs correctly if the operation type changes (e.g. Create -> Update)
                if self.crud_intent_answer.create.value:
                    self.operation_id = self.crud_intent_answer.create.operation_id
                elif self.crud_intent_answer.update.value:
                    self.operation_id = self.crud_intent_answer.update.operation_id
                elif self.crud_intent_answer.delete.value:
                    self.operation_id = self.crud_intent_answer.delete.operation_id

                # if more cycles are required to collect information, the method sets cycle_is_ready=False
                envelope_api, cycle_is_ready = write_action_to_entity(self)

                # Clear operation_ids when operations complete (only for create/update/delete)
                if cycle_is_ready:
                    self.operation_id = None
                    if self.crud_intent_answer.create.value:
                        self.crud_intent_answer.create.operation_id = ""
                    elif self.crud_intent_answer.update.value:
                        self.crud_intent_answer.update.operation_id = ""
                    elif self.crud_intent_answer.delete.value:
                        self.crud_intent_answer.delete.operation_id = ""

            # Read operation
            elif self.crud_intent_answer.show.value:
                envelope_api = read_action_to_entity(self)
                # Show is stateless, ensure no operation_id hangs around (though it shouldn't)
                self.operation_id = None

            # Read operation with interpretation in the second llm call
            else:
                # No explicit CRUD intent detected at the start of a conversation => NONE
                self.system_prompt = dumps_for_llm_prompt(Prompt.GET_FUNCTION_CALL.value)
                self.system_prompt_name = Prompt.GET_FUNCTION_CALL.name
                envelope_api = self.llm_client.general_answer_assistant.answer_general_question(self)
                self.operation_id = None

                if not envelope_api:
                    trace_id = log_error(ErrorCode.LLM_ERROR_EMPTY_ANSWER)
                    raise APIError(ErrorCode.LLM_ERROR_EMPTY_ANSWER, trace_id)

            # Read operations do not have the feedback to the LLM

            # save the envelope for the feedback to the LLM
            self.result = (envelope_api.model_dump(mode='json'), cycle_is_ready)

            return envelope_api

        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except RequestException:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, exception=error)
            raise APIError(ErrorCode.ERROR_PERFORMING_CRUD_OPERATION, trace_id) from error