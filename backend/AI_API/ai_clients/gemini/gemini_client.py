import json
import os
from google.genai import types
from abc import ABC

from ApartmentManager.backend.AI_API.ai_clients.gemini.booleanOutput import BooleanOutput
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call import FunctionCallService
from ApartmentManager.backend.AI_API.ai_clients.gemini.structured_output import StructuredOutput
from google import genai
from dotenv import load_dotenv

from ApartmentManager.backend.AI_API.general.errors import ErrorCode
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

    def get_structured_llm_response(self, user_question: str) -> dict:
        llm_response = self.structured_output_service.get_structured_llm_response(user_question)
        return llm_response

    def get_textual_llm_response(self, user_question: str) -> dict:
        pass

    def interpret_llm_response_from_conversation(self) -> dict:
        """
        Interprets the structured output data from the conversation history and
        retrieve a response with human-like text.
        :return: Interpretation of a machine like response from the LLM (struct output).
        """

        # Configuration of the creativity
        config_llm_text_answer = types.GenerateContentConfig(
            temperature=self.temperature # for stable answers
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
            print(ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, ": ", error)
            return {
                "type": "text",
                "result": {
                    "message": llm_answer
                },
                "meta": {
                    "model": self.model_name
                },
                "error": {"code": ErrorCode.LLM_RESPONSE_INTERPRETATION_ERROR, "message": str(error)}
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