import os
from abc import ABC

from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call import FunctionCallService
from ApartmentManager.backend.AI_API.ai_clients.gemini.structured_output import StructuredOutput
from google import genai
from dotenv import load_dotenv
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.AI_API.general.ai_client import AIClient

class GeminiClient:
    #class GeminiClient(AIClient, ABC):
    """
    Client implementation for interacting with the Gemini AI model.
    This class provides methods to interface with a RESTful API. It inherits from
    the abstract base class AIClient and implements all required methods.
    """
    # Specify the model to use
    model_name = "gemini-2.5-flash"

    def __init__(self):
        # Load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

        # Create an object to let the AI Model call functions
        self.function_call_service = FunctionCallService(self.client, self.model_name)

        # Create an object to let the AI get the answer as predefined JSON
        self.structured_output_service = StructuredOutput(self.client, self.model_name)

    def process_function_call_request(self, user_question):
        return self.function_call_service.response_with_ai_function_call(user_question)

    def get_structured_ai_response(self, prompt: str) -> dict:
        return self.structured_output_service.get_structured_ai_response(prompt)