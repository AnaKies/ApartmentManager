import os
from google import genai
from dotenv import load_dotenv
import ApartmentManager.backend.AI_API.general.prompting as prompting

# load variables from environment
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# Specify the model to use
model_flash = "gemini-2.5-flash"

response_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "filters": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of columns to filter the SQL table."
        }
    },
    "required": ["path", "filters"]
}

def generate_structured_ai_response(extended_prompt):
    """
    Generates a structured response according to the given JSON scheme.
    :param extended_prompt: User's prompt extended for a command to generate JSON data for the later query.
    :return: JSON scheme containing keywords "path" and "filters for later using in a query.
    """
    response = client.models.generate_content(
        model=model_flash,
        contents=extended_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema
        }
    )
    return response.parsed

def generate_human_like_ai_response(extended_prompt):
    """
    Generates a human like response to the user's question using the retrieved data from the SQL data bank.
    :param extended_prompt: User#s prompt extended for retrieved data from the SQL data bank.
    :return: Human like response to the user's question.
    """
    # AI answers in a human like message
    response = client.models.generate_content(
        model=model_flash,
        contents=extended_prompt)
    return response.text


def ai_generate_json_data_for_sql_query(user_question):
    """
    AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
    :param user_question: user input to the AI
    :return: JSON data used for a query
    """

    generated_query_as_json =  prompting.ai_generate_query(user_question, generate_structured_ai_response)
    return generated_query_as_json


def call_endpoint_restful_api(json_data_for_restful_api_request):
    """
    Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
    :param json_data_for_restful_api_request: JSON with keys "path" and "filters for a query to an endpoint RESTFUL API.
    :return: JSON response from the endpoint RESTFUL API
    """
    response_json_from_restful_api = prompting.execute_restful_api_query(json_data_for_restful_api_request)
    return response_json_from_restful_api

def represent_ai_answer(restful_api_response, user_question):
    """
    Generates a human like answer to a user question using retrieved data from the SQL data bank.
    :param restful_api_response: Data from the SQL data bank
    :param user_question: User's question
    :return: Human like text containing an answer to the user's question.
    """
    human_like_ai_answer = prompting.ai_represent_answer(restful_api_response,
                                                         user_question,
                                                         generate_human_like_ai_response)
    return human_like_ai_answer



while True:
    # User asks a question
    user_question = input("Ask me something about apartments: ")

    # AI generates a query
    query_json = ai_generate_json_data_for_sql_query(user_question)
    print("......AI generated query:", query_json)

    # Python script executes the query
    api_response = call_endpoint_restful_api(query_json)
    print("......RESTFUL API returned data:", api_response)

    # AI generates a human friendly answer
    ai_answer = represent_ai_answer(api_response, user_question)
    print(ai_answer)
