import json
import os
from google.genai import types
from abc import ABC

from ApartmentManager.backend.AI_API.ai_clients.gemini.booleanOutput import BooleanOutput
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call import FunctionCallService
from ApartmentManager.backend.AI_API.ai_clients.gemini.structured_output import StructuredOutput
from google import genai
from dotenv import load_dotenv

from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.errors_backend import ErrorCode
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Contract, Tenancy, Apartment
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.AI_API.general.ai_client import LlmClient

class GeminiClient:
    #class GeminiClient(AIClient, ABC):
    """
    Client implementation for interacting with the Gemini LLM model.
    This class provides methods to interface with a RESTful API. It inherits from
    the abstract base class LLM-Client and implements all required methods.
    """

    def __init__(self):
        # Load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

        # Specify the model to use
        self.model_name = "gemini-2.5-flash"

        # Specify creativity of LLM answers (0 ... 2)
        self.temperature = 0.3

        # volatile memory of the conversation
        self.session_contents: list[types.Content] = []

        # Create an object to let the LLM Model call functions
        self.function_call_service = FunctionCallService(self.client,
                                                         self.model_name,
                                                         self.session_contents,
                                                         self.temperature)

        # Create an object to let the LLM get the answer as predefined JSON
        self.structured_output_service = StructuredOutput(self.client,
                                                          self.model_name,
                                                          self.session_contents,
                                                          self.temperature)

        # Create an object to let the LLM answer with boolean true/false
        self.boolean_output_service = BooleanOutput(self.client,
                                                    self.model_name,
                                                    self.session_contents,
                                                    self.temperature)

    def process_function_call_request(self, user_question, system_prompt: str) -> dict:
        """
        Gives the user a response using data, retrieved from a function, being called by LLM.
        :param user_question: Question from the user
        :param system_prompt: Combined system prompt
        :return: JSON with human like text answer containing the data retrieved from the function.
        If no function call is made, returns a plain text answer with the reason why it was not possible.
        """
        func_call_response = self.function_call_service.try_call_function(user_question, system_prompt)

        return func_call_response

    def add_new_entry_to_database(self, user_question) -> dict:
        return {}

    def get_textual_llm_response(self, user_question: str, system_prompt: str) -> dict:
        # Add the user prompt to the summary request to LLM
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(
            role="user",
            parts=[user_part]
        )
        self.session_contents.append(user_part_content)
        result = self.interpret_llm_response_from_conversation(system_prompt=system_prompt)

        return result

    def interpret_llm_response_from_conversation(self, system_prompt: str) -> dict:
        """
        Interprets the structured output data from the conversation history and
        retrieve a response with human-like text.
        :param system_prompt:
        :return: Interpretation of a machine like response from the LLM (struct output).
        """

        # Configuration of the LLM answer with a new system instruction
        config_llm_text_answer = types.GenerateContentConfig(
            temperature=self.temperature, # for stable answers
            system_instruction=types.Part(text=system_prompt)
        )

        llm_answer = None
        try:
            llm_response_with_text_answer = self.client.models.generate_content(
                model=self.model_name,
                config=config_llm_text_answer,
                contents=self.session_contents
            )
            text_answer = llm_response_with_text_answer.candidates[0].content
            # Place the answer of the LLM in the conversation history.
            self.session_contents.append(text_answer)

            if text_answer:
                for part in text_answer.parts:
                    # part can be text, function_call, thought_signature etc.
                    if hasattr(part, "text") and part.text:
                        llm_answer = part.text
                        break
            return {
                "type": "text",
                "result": {
                    "message": llm_answer
                },
                "meta": {
                    "model": self.model_name
                }
            }
        except Exception as error:
            print(ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, ": ", repr(error))
            return {
                "type": "error",
                "result": {
                    "message": llm_answer
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR + ": " + repr(error)}
            }

    def get_crud_in_user_question(self, user_question: str) -> dict:
        """
        Returns the boolean answer True or False for every CRUD
        operation possibly noticed in the user question.
        :param user_question: Question from the user.
        :return: Boolean value True or False for keys "add", "delete", "update", "show".

        """
        crud_intent_dict = self.boolean_output_service.get_boolean_llm_response(user_question)
        return crud_intent_dict

    def generate_prompt_for_create_entity(self, crud_intent: dict) -> str | dict:
        """
        Analyzes the CRUD intent for creation an entity (person, contract ect.)
        and generates a system prompt containing dynamic fields for an entity.
        :param crud_intent: Dictionary containing which CRUD operations that should be done.
        When an operation is "CREATE" = True, then which entity should be created.
        :return: System prompt extended with fields
        """
        create_entity_active = (crud_intent.get("create") or {}).get("value", False)
        system_prompt = None
        try:
            #Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
            if create_entity_active:
                type_of_data = (crud_intent or {}).get("create").get("type", "")
                if type_of_data == "person":
                    class_fields = PersonalData.fields_dict()
                elif type_of_data == "contract":
                    class_fields = Contract.fields_dict()
                elif type_of_data == "tenancy":
                    class_fields = Tenancy.fields_dict()
                elif type_of_data == "apartment":
                    class_fields = Apartment.fields_dict()
                else:
                    raise Exception("Error: not allowed fields for creating new entry in database.")

                if class_fields:
                    # Inject the class fields in a prompt
                    system_prompt = prompting.inject_fields_to_create_prompt(class_fields)

                return system_prompt
            return None
        except Exception as error:
            print(ErrorCode.ERROR_INJECTING_FIELDS_TO_PROMPT + " :", repr(error))
            return {
                "type": "error",
                "result": {
                    "message": system_prompt
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.ERROR_INJECTING_FIELDS_TO_PROMPT + ": " + repr(error)}
            }

    def answer_general_questions(self, user_question: str, system_prompt: str) -> dict:
        """
        Analyzes if the GET operation is required and performs the function call to retrieve the data from the databank.
        Then convert the data to the plain text.
        If no data bank calling was done, then it responds to the question directly.
        :param user_question: Question from the user.
        :param system_prompt: System prompt with instructions for function calling.
        :return: Data from the database as dictionary.
        """
        result = None
        llm_answer_in_text_format = None
        func_call_data_or_llm_text_dict = None

        try:
            # STEP 1: LLM generates an answer as dict with possible function call inside using GET tool
            func_call_data_or_llm_text_dict = self.process_function_call_request(user_question, system_prompt)

            func_result = (func_call_data_or_llm_text_dict or {}).get("result")
            has_func_call_flag = (func_result or{}).get("function_call")
            llm_answer_in_text_format = not has_func_call_flag

        except Exception as error:
            print(ErrorCode.ERROR_CALLING_FUNCTION + " :", repr(error))
            return {
                "type": "error",
                "result": {
                    "message": func_call_data_or_llm_text_dict
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.ERROR_CALLING_FUNCTION + ": " + repr(error)}
            }

        try:
            # Scenario 1: LLM answered with plain text without function call
            # or result of answer were the structured data.
            if llm_answer_in_text_format:
                # Returns the structured output or
                # Dictionary with reason why the LLM decided not to call a function.
                result = func_call_data_or_llm_text_dict

            # Scenario 2: LLM answered with function call and this answer should be interpreted
            else:
                # LLM is interpreting the data from function call to the human language.
                # Dictionary with data for the interpretation is taken from the conversation history.
                result = self.get_textual_llm_response(user_question, system_prompt)
        except Exception as error:
            print(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL + " :",repr(error))
            return {
                "type": "error",
                "result": {
                    "message": result
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL +" :" + repr(error)}
            }

        # STEP 2: Unified logging
        llm_answer_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        try:
            func_result = (func_call_data_or_llm_text_dict or {}).get("result", {})
            is_func_call = (func_result or {}).get("function_call")
            request_type = "function call" if is_func_call else "plain text"

            if is_func_call:
                payload_result = func_result.get("payload")
                payload_result_str = json.dumps(payload_result, indent=2, ensure_ascii=False, default=str)
                backend_response_str = payload_result_str if payload_result_str is not None else "---"
            else:
                backend_response_str = "---"

            create_new_log_entry(
                llm_model=self.model_name,
                user_question=user_question or "---",
                request_type=request_type,
                backend_response=backend_response_str,
                llm_answer=llm_answer_str
            )
        except Exception as error:
            print(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING + " :",repr(error))

        return result

    def process_show_request(self, user_question: str, system_prompt: str) -> dict | None:
        """
        Analyzes if the user question contains the data type, that should be shown.
        Asks the user for missing data type if it is not in the show request.
        It uses a predefined scheme for checking fields.
        :param user_question: Question from the user.
        :param system_prompt: System prompt with instructions for gathering missing data.
        :return: Dictionary structure with check status and data type.
        # The answer structure corresponds the predefined scheme.
        """
        display_data_scheme = types.Schema(
            title="data_to_show",
            type=types.Type.OBJECT,
            properties={
                "checked": types.Schema(type=types.Type.BOOLEAN),
                "type": types.Schema(
                    any_of=[
                        types.Schema(type=types.Type.STRING),
                        types.Schema(type=types.Type.NULL)
                    ]
                )
            },
            required=["checked", "type"]
        )

        llm_response = None
        try:
            llm_response = self.structured_output_service.get_structured_llm_response(user_question,
                                                                                      system_prompt,
                                                                                      display_data_scheme)
            return llm_response

        except Exception as error:
            print(ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW + " :", repr(error))
            return {
                "type": "error",
                "result": {
                    "message": llm_response
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW + " :" + repr(error)}
            }

    def process_create_request(self, user_question: str, system_prompt: str) -> dict | None:
        """
        Calls the LLM with the system prompt extended to the class fields.
        The provided scheme normalizes the returned answer.
        :param user_question: Question from the user.
        :param system_prompt: System prompt with instructions for gathering missing data.
        :return: Dictionary with check status and data type according to the provided scheme.
        """
        create_data_scheme = types.Schema(
            title="create_entity",
            type=types.Type.OBJECT,
            properties={
                "ready_to_post": types.Schema(type=types.Type.BOOLEAN),
                "data": types.Schema(type=types.Type.STRING),
                "comment": types.Schema(type=types.Type.STRING),
            },
            required=["ready_to_post", "data", "comment"]
        )

        try:
            llm_response = self.structured_output_service.get_structured_llm_response(user_question,
                                                                                      system_prompt,
                                                                                      create_data_scheme)
            return llm_response

        except Exception as error:
            print(ErrorCode.LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY + " :", repr(error))
            return {
                "type": "error",
                "result": {
                    "message": "LLM could not generate a response."
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY + " :" + repr(error)}
            }