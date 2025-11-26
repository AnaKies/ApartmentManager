import os
from google.genai import types
from abc import ABC
from google.genai import errors as genai_errors
from ApartmentManager.backend.AI_API.ai_clients.gemini.crud_intent_assistant import CrudIntentAssistant
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call_assistant import FunctionCallAssistant
from ApartmentManager.backend.AI_API.ai_clients.gemini.write_actions_assistant import WriteActionsAssistant
from google import genai
from dotenv import load_dotenv
from ApartmentManager.backend.AI_API.ai_clients.gemini.general_answer_assistant import GeneralAnswerAssistant


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
        self.function_call_assistant = FunctionCallAssistant(llm_client=self.client,
                                                             model_name=self.model_name,
                                                             session_contents=self.session_contents,
                                                             temperature=self.temperature)


        # Create an object to let the LLM decide whether the user question has CRUD intent
        self.crud_intent_assistant = CrudIntentAssistant(llm_client=self.client,
                                                         model_name=self.model_name,
                                                         session_contents=self.session_contents,
                                                         temperature=self.temperature)

        # Create an object to let the LLM collect required data for the appropriate CRUD operation
        self.write_actions_assistant = WriteActionsAssistant(llm_client=self.client,
                                                             model_name=self.model_name,
                                                             session_contents=self.session_contents,
                                                             temperature=self.temperature,
                                                             crud_intent=self.crud_intent_assistant,
                                                             function_call=self.function_call_assistant)

        # Create an object to let the LLM answer general questions using DB data or not
        self.general_answer_assistant = GeneralAnswerAssistant(llm_client=self.client,
                                                               model_name=self.model_name,
                                                               session_contents=self.session_contents,
                                                               temperature=self.temperature,
                                                               function_call_service=self.function_call_assistant)