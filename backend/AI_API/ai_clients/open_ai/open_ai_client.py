import os
from dotenv import load_dotenv
from openai import OpenAI
from ApartmentManager.backend.AI_API.general.ai_client import AIClient

class OpenAiClient(AIClient):
    # Specify the model to use
    model_name = "gpt-5"
    client = None

    def __init__(self):
        # load variables from environment
        load_dotenv()

        # Get API key from environment
        open_ai_api_key = os.getenv("OPEN_AI_KEY")

        self.client = OpenAI(api_key=open_ai_api_key)

    def get_structured_ai_response(self, ai_role_prompt: str, user_question: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param: ai_role_prompt: The prompt for the AI behavior.
        :param: user_question: The prompt with user question.
        :return: JSON scheme containing keywords "path" and "filters for later using in a query.
        """
        response = self.client.responses.create(model=self.model_name, inout=user_question + ai_role_prompt)



    def get_human_like_ai_response(self, ai_role_prompt: str, user_prompt_with_sql: str) -> str:
        """
        Generates a human like response to the user's question using the retrieved data from the SQL data bank.
        :param ai_role_prompt: The prompt for the AI behavior.
        :param user_prompt_with_sql: User's prompt extended for retrieved data from the SQL data bank.
        :return: Human like response to the user's question.
        """


    def ai_generate_json_data_for_sql_query(self, user_question: str) -> dict:
        """
        AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
        :param user_question: user input to the AI
        :return: JSON data used for a query
        """


    def call_endpoint_restful_api(self, json_data_for_restful_api_request: dict) -> dict:
        """
        Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
        :param json_data_for_restful_api_request: JSON with keys "path" and "filters for a query to an endpoint RESTFUL API.
        :return: JSON response from the endpoint RESTFUL API
        """


    def represent_ai_answer(self, restful_api_response: dict, user_question: str) -> str:
        """
        Generates a human like answer to a user question using retrieved data from the SQL data bank.
        :param restful_api_response: Data from the SQL data bank
        :param user_question: User's question
        :return: Human like text containing an answer to the user's question.
        """
