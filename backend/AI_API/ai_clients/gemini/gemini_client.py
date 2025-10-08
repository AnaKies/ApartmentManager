import os
from google.genai import types
from abc import ABC

from ApartmentManager.backend.AI_API.ai_clients.gemini.booleanOutput import BooleanOutput
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call import FunctionCallService
from ApartmentManager.backend.AI_API.ai_clients.gemini.structured_output import StructuredOutput
from google import genai
from dotenv import load_dotenv
from ApartmentManager.backend.AI_API.general.ai_client import AIClient

class GeminiClient:
    #class GeminiClient(AIClient, ABC):
    """
    Client implementation for interacting with the Gemini AI model.
    This class provides methods to interface with a RESTful API. It inherits from
    the abstract base class AIClient and implements all required methods.
    """

    def __init__(self):
        # Load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

        # Specify the model to use
        self.model_name = "gemini-2.5-flash"

        # Specify creativity of AI answers (0 ... 2)
        self.temperature = 0.3

        # volatile memory of the conversation
        self.session_contents: list[types.Content] = []

        # Create an object to let the AI Model call functions
        self.function_call_service = FunctionCallService(self.client,
                                                         self.model_name,
                                                         self.session_contents,
                                                         self.temperature)

        # Create an object to let the AI get the answer as predefined JSON
        self.structured_output_service = StructuredOutput(self.client,
                                                          self.model_name,
                                                          self.session_contents,
                                                          self.temperature)

        # Create an object to let the AI answer with boolean true/false
        self.boolean_output_service = BooleanOutput(self.client,
                                                    self.model_name,
                                                    self.session_contents,
                                                    self.temperature)

    def process_function_call_request(self, user_question) -> dict:
        """
        Gives the user a response using data, retrieved from a function, being called by AI.
        :param user_question: Question from the user
        :return: JSON with human like text answer containing the information from the SQL data bank
        """
        ai_response = self.function_call_service.try_response_using_function_call_data(user_question)
        return ai_response

    def get_structured_ai_response(self, user_question: str) -> dict:
        ai_response = self.structured_output_service.get_structured_ai_response(user_question)
        return ai_response

    def get_textual_ai_response(self, user_question: str) -> dict:
        pass

    def get_boolean_answer(self, user_question: str) -> dict:
        """
        Returns the boolean answer True or False.
        :param user_question: Question from the user.
        :return: F.e { "result": True }
        """
        ai_response = self.boolean_output_service.get_boolean_ai_response(user_question)
        return ai_response

