import os
import json
import re
import requests
from google import genai
from dotenv import load_dotenv
from ApartmentManager.backend.config.server_config import HOST, PORT

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

def ai_generate_query(user_question):
    """
    AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
    :param user_question: user input to the AI
    :return: JSON data used for a query
    """
    prompt = f"""
    You are an AI assistant connected to a system API manager.
    You know the following API paths:
    1. /apartments
    2. /tenancies
    3. /persons

    Rules:
    - If the user's question mentions 'apartments', generate a query to fetch data from the /apartments API.
    - Output ONLY a JSON object with keys:
      - "path": API path to call
      - "filters": dictionary of query parameters (optional)
    - Do not generate human-readable text here; only generate the query.

    User question: "{user_question}"
    """
    # structured output to get pure JSON
    response = client.models.generate_content(
        model=model_flash,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema
        }
    )
    return response.parsed

def execute_api_query(json_data_for_query):
    """
    Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
    :param json_data_for_query: JSON with keys "path" and "filters
    :return: JSON response from the endpoint RESTFUL API
    """
    try:
        path = json_data_for_query["path"]

        if not path:
            raise ValueError("No path provided")

        # list of columns to filter the SQL table
        filters = json_data_for_query.get("filters", [])
        url = f"http://{HOST}:{PORT}{path}"

        response = requests.get(url)
        return response.json()
    except Exception as error:
        print(error)
        return None

def ai_represent_answer(restful_api_response, user_question):
    """
    Generates a human like answer to a user question using retrieved data from the SQL data bank.
    :param restful_api_response: Data from the SQL data bank
    :param user_question: User's question
    :return: Human like text containing an answer to the user's question.
    """
    if restful_api_response:
        prompt = f"""
        User asked: "{user_question}"
        API returned the following data: {restful_api_response}
        Generate a friendly answer to the user based on the real data.
        """
    else:
        prompt = f"""
        User asked: "{user_question}"
        The database did not return any useful data for this query.
        Please answer the question as best as you can, without relying on database results.
        """

    # AI answers in a human like message
    response = client.models.generate_content(
        model=model_flash,
        contents=prompt)
    return response.text



while True:
    # User asks a question
    user_question = input("Ask me something about apartments: ")

    # AI generates a query
    query_json = ai_generate_query(user_question)
    print("......AI generated query:", query_json)

    # Python script executes the query
    api_response = execute_api_query(query_json)
    print("......RESTFUL API returned data:", api_response)

    # AI generates a human friendly answer
    ai_answer = ai_represent_answer(api_response, user_question)
    print(ai_answer)
