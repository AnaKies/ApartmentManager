import json
import typing
from google import genai
from google.genai import errors as genai_errors, types
from requests import RequestException
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import AnswerSource, EnvelopeApi, TextResult, \
    DataResult
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call_assistant import FunctionCallAssistant
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import build_text_answer
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry

class GeneralAnswerAssistant:
    def __init__(self,
                 llm_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float,
                 function_call_service: FunctionCallAssistant):
        """
        Service for requesting structured JSON output from the LLM model.
        """
        self.client = llm_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature
        self.function_call_service = function_call_service


    def answer_general_question(self, conversation_client: "ConversationClient") -> EnvelopeApi:
        """
        Analyzes if the GET operation is required and performs the function call to retrieve the data from the databank.
        Then convert the data to the plain text.
        If no data bank calling was done, then it responds to the question directly.
        :param conversation_client:
        :param system_prompt: System prompt with instructions for function calling.
        :return: Data from the database as a dictionary.
        """

        try:
            # STEP 1: LLM generates an answer as dict with the possible function call inside using GET tool
            func_call_data_or_llm_text_dict = self.function_call_service.try_call_function(conversation_client)

            func_result_data_or_text = func_call_data_or_llm_text_dict.result

            llm_answer_in_text_format = False

            if isinstance(func_result_data_or_text, TextResult):
                llm_answer_in_text_format = True

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
                result = self.get_textual_llm_response(conversation_client)
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL, exception=error)
            raise APIError(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL, trace_id) from error

        # STEP 2: Unified logging
        llm_answer_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        try:
            func_result_data_or_text = func_call_data_or_llm_text_dict.result

            is_func_call = False
            if isinstance(func_result_data_or_text, DataResult):
                is_func_call = func_result_data_or_text.function_call

            request_type = "function call" if is_func_call else "plain text"

            if is_func_call:
                payload_result = func_result_data_or_text.payload
                payload_result_str = json.dumps(payload_result, indent=2, ensure_ascii=False, default=str)
                backend_response_str = payload_result_str if payload_result_str is not None else "---"
            else:
                backend_response_str = "---"

            create_new_log_entry(
                llm_model=self.model,
                user_question=conversation_client.user_question or "---",
                request_type=request_type,
                backend_response=backend_response_str,
                llm_answer=llm_answer_str,
                system_prompt_name=conversation_client.system_prompt_name
            )
        except Exception as error:
            trace_id = log_error(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING, exception=error)
            raise APIError(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING, trace_id) from error

        return result


    def get_textual_llm_response(self, conversation_client: "ConversationClient") -> EnvelopeApi:
        # Add the user prompt to the summary request to LLM
        user_part = types.Part(text=conversation_client.user_question)
        user_part_content = types.Content(
            role="user",
            parts=[user_part]
        )
        self.session_contents.append(user_part_content)
        result = self.interpret_llm_response_from_conversation(system_prompt=conversation_client.system_prompt)

        return result

    def interpret_llm_response_from_conversation(self, system_prompt: str) -> EnvelopeApi:
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
                model=self.model,
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
                                           model=self.model,
                                           answer_source=AnswerSource.LLM)
            else:
                trace_id = log_error(ErrorCode.LLM_ERROR_NO_TEXT_ANSWER)
                raise APIError(ErrorCode.LLM_ERROR_NO_TEXT_ANSWER, trace_id)

            return result

        except APIError:
            raise
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, exception=error)
            raise APIError(ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, trace_id) from error