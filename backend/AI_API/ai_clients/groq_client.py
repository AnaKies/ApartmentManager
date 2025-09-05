import os
import json
from groq import Groq
from dotenv import load_dotenv
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.AI_API.general.ai_client import AIClient
from ApartmentManager.backend.AI_API.general.structured_output import response_schema_groq, QuerySchema

# System's task
system_prompt = "You are a helpful assistant."

class GroqClient(AIClient):
    # Specify the model to use
    model_name = "openai/gpt-oss-20b"
    client = None

    def __init__(self):
        # load variables from environment
        load_dotenv()

        # Get API key from environment
        groq_api_key = os.getenv("GROQ_API_KEY")

        # Initialize the Groq client
        self.client = Groq(api_key=groq_api_key)

    def transport_structured_ai_response(self, extended_prompt: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param extended_prompt: User's prompt extended for a command to generate JSON data for the later query.
        :return: JSON scheme containing keywords "path" and "filters for later using in a query.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extended_prompt}
            ],
            response_format=response_schema_groq
        )
        json_string_for_sql_query = response.choices[0].message.content
        try:
            # Convert string representation of JSON to dictionary
            json_for_sql_query = json.loads(json_string_for_sql_query)
            valid_json_obj_for_sql_query = QuerySchema.model_validate(json_for_sql_query)
            dict_for_sql_query = valid_json_obj_for_sql_query.model_dump()

        except json.decoder.JSONDecodeError as error:
            print("Failed to parse JSON from AI response.", error)
            print("Original response:", json_for_sql_query)
            dict_for_sql_query = {} # prohibit to return the false data to the next function
        return dict_for_sql_query

    def transport_human_like_ai_response(self, extended_prompt: str) -> str:
        """
        Generates a human like response to the user's question using the retrieved data from the SQL data bank.
        :param extended_prompt: User#s prompt extended for retrieved data from the SQL data bank.
        :return: Human like response to the user's question.
        """

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": extended_prompt}
            ]
        )
        return response.choices[0].message.content


    def ai_generate_json_data_for_sql_query(self, user_question: str) -> dict:
        """
        AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
        :param user_question: user input to the AI
        :return: JSON data used for a query
        """

        generated_query_as_json =  prompting.ai_generate_query(user_question,
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