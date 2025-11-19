import json
import os
from google.genai import types
from abc import ABC
from google.genai import errors as genai_errors
from requests import RequestException
from ApartmentManager.backend.AI_API.ai_clients.gemini.booleanOutput import BooleanOutput
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call import FunctionCallService
from ApartmentManager.backend.AI_API.ai_clients.gemini.structured_output import StructuredOutput
from google import genai
from dotenv import load_dotenv

from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.api_envelopes import build_text_answer
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Contract, Tenancy, Apartment
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.AI_API.general.error_texts import APIError

class GeminiClient:
    #class GeminiClient(AIClient, ABC):
    """
    Client implementation for interacting with the Gemini LLM model.
    This class provides methods to interface with a RESTful API. It inherits from
    the abstract base class LLM-Client and implements all required methods.
    """

    def __init__(self, some_gemini_model: str):
        # Load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

        # Specify the model to use
        self.model_name = some_gemini_model

        # Specify creativity of LLM answers (0 ... 2)
        self.temperature = 0.3 # for precise answers

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
        :return: JSON with human-like text answer containing the data retrieved from the function.
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

            if llm_answer:
                result = build_text_answer(message=llm_answer,
                                           model=self.model_name,
                                           answer_source="llm")
            else:
                trace_id = log_error(ErrorCode.LLM_ERROR_NO_TEXT_ANSWER)
                raise APIError(error_code_obj=ErrorCode.LLM_ERROR_NO_TEXT_ANSWER,
                               trace_id=trace_id)

            return result

        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, exception=error)
            raise APIError(error_code_obj=ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR,
                           trace_id=trace_id) from error

    def get_crud_in_user_question(self, user_question: str) -> dict:
        """
        Returns the boolean answer True or False for every CRUD
        operation possibly noticed in the user question.
        :param user_question: Question from the user.
        :return: Boolean value True or False for keys "add", "delete", "update", "show".

        """
        crud_intent_dict = self.boolean_output_service.get_boolean_llm_response(user_question)
        return crud_intent_dict


    def answer_general_questions(self, user_question: str, system_prompt: str) -> dict:
        """
        Analyzes if the GET operation is required and performs the function call to retrieve the data from the databank.
        Then convert the data to the plain text.
        If no data bank calling was done, then it responds to the question directly.
        :param user_question: Question from the user.
        :param system_prompt: System prompt with instructions for function calling.
        :return: Data from the database as a dictionary.
        """

        try:
            # STEP 1: LLM generates an answer as dict with the possible function call inside using GET tool
            func_call_data_or_llm_text_dict = self.process_function_call_request(user_question, system_prompt)

            func_result = (func_call_data_or_llm_text_dict or {}).get("result")
            has_func_call_flag = (func_result or{}).get("function_call")
            llm_answer_in_text_format = not has_func_call_flag
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except RequestException:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.ERROR_CALLING_FUNCTION, exception=error)
            raise APIError(ErrorCode.ERROR_CALLING_FUNCTION, trace_id) from error

        try:
            # Scenario 1: LLM answered with plain text without function call,
            # or the result of the answer was the structured data.
            if llm_answer_in_text_format:
                # Returns the structured output or
                # Dictionary with the reason why the LLM decided not to call a function.
                result = func_call_data_or_llm_text_dict

            # Scenario 2: LLM answered with a function call, and this answer should be interpreted
            else:
                # LLM is interpreting the data from a function call to the human language.
                # Dictionary with data for the interpretation is taken from the conversation history.
                result = self.get_textual_llm_response(user_question, system_prompt)
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL, exception=error)
            raise APIError(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL, trace_id) from error

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
            trace_id = log_error(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING, exception=error)
            raise APIError(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING, trace_id) from error

        return result

    def process_delete_request(self, user_question: str, system_prompt: str) -> dict | None:
        delete_data_scheme = types.Schema(
            title="delete_entity",
            type=types.Type.OBJECT,
            properties={
                "ready_to_delete": types.Schema(type=types.Type.BOOLEAN),
                "data": types.Schema(type=types.Type.STRING),
                "comment": types.Schema(type=types.Type.STRING),
            },
            required=["ready_to_delete", "data", "comment"]
        )
        try:
            llm_response = self.structured_output_service.get_structured_llm_response(user_question,
                                                                                      system_prompt,
                                                                                      delete_data_scheme)
            return llm_response
        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW, exception=error)
            raise APIError(ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW, trace_id) from error


    def process_show_request(self, user_question: str, system_prompt: str) -> dict | None:
        """
        Analyzes if the user question contains the data type, that should be shown.
        Asks the user for the missing data type if it is not in the show request.
        It uses a predefined scheme for checking fields.
        :param user_question: Question from the user.
        :param system_prompt: System prompt with instructions for gathering missing data.
        :return: Dictionary structure with check status and data type.
        # The answer structure corresponds to the predefined scheme.
        """
        display_data_scheme = types.Schema(
            title="data_to_show",
            type=types.Type.OBJECT,
            properties={
                "checked": types.Schema(type=types.Type.BOOLEAN), # True if in the sentence there exists an entity to show
                "type": types.Schema( # What should be shown (apartments, persons etc.)
                    any_of=[
                        types.Schema(type=types.Type.STRING),
                        types.Schema(type=types.Type.NULL)
                    ]
                )
            },
            required=["checked", "type"]
        )

        try:
            llm_response = self.structured_output_service.get_structured_llm_response(user_question,
                                                                                      system_prompt,
                                                                                      display_data_scheme)
            return llm_response
        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW, exception=error)
            raise APIError(ErrorCode.LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW, trace_id) from error

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
        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY, exception=error)
            raise APIError(ErrorCode.LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY, trace_id) from error