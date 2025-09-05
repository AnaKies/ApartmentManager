import os
from google import genai
from dotenv import load_dotenv
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.AI_API.general.ai_client import AIClient
from ApartmentManager.backend.AI_API.general.structured_output import response_schema_gemini, QuerySchema

class GeminiClient(AIClient):
    """
    Client implementation for interacting with the Gemini AI model.
    This class provides methods to generate structured JSON responses for SQL queries,
    human-like textual answers, and to interface with a RESTful API. It inherits from
    the abstract base class AIClient and implements all required methods.
    """
    # Specify the model to use
    model_name = "gemini-2.5-flash"
    client = None

    def __init__(self):
        # load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

    def transport_structured_ai_response(self, ai_role_prompt: str, user_question: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param: ai_role_prompt: The prompt for the AI behavior.
        :param: user_question: The prompt with user question.
        :return: JSON scheme containing keywords "path" and "filters for later using in a query.
        """
        json_string_for_sql_query = self.client.models.generate_content(
            model=self.model_name,
            contents=ai_role_prompt+user_question,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema_gemini
            }
        )
        # Convert string representation of JSON to dictionary
        dict_for_sql_query = json_string_for_sql_query.parsed
        return dict_for_sql_query

    def transport_human_like_ai_response(self, ai_role_prompt: str, user_prompt_with_sql: str) -> str:
        """
        Generates a human like response to the user's question using the retrieved data from the SQL data bank.
        :param ai_role_prompt: The prompt for the AI behavior.
        :param user_prompt_with_sql: User's prompt extended for retrieved data from the SQL data bank.
        :return: Human like response to the user's question.
        """
        # AI answers in a human like message
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=ai_role_prompt + user_prompt_with_sql)
        return response.text


    def ai_generate_json_data_for_sql_query(self, user_question: str) -> dict:
        """
        AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
        :param user_question: user input to the AI
        :return: JSON data used for a query
        """

        generated_query_as_json = prompting.ai_generate_query(user_question,
                                                              self.transport_structured_ai_response)
        return generated_query_as_json


    def call_endpoint_restful_api(self, json_data_for_restful_api_request: dict) -> dict:
        """
        Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
        :param json_data_for_restful_api_request: JSON with keys "path" and "filters for a query to an endpoint RESTFUL API.
        :return: JSON response from the endpoint RESTFUL API
        """
        response_json_from_restful_api = prompting.execute_restful_api_query(json_data_for_restful_api_request)

        return response_json_from_restful_api


    def represent_ai_answer(self, restful_api_response: dict, user_question: str) -> str:
        """
        Generates a human like answer to a user question using retrieved data from the SQL data bank.
        :param restful_api_response: Data from the SQL data bank
        :param user_question: User's question
        :return: Human like text containing an answer to the user's question.
        """
        human_like_ai_answer = prompting.ai_represent_answer(restful_api_response,
                                                             user_question,
                                                             self.transport_human_like_ai_response)
        return human_like_ai_answer