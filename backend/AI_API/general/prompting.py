from ApartmentManager.backend.config.server_config import HOST, PORT
import requests

system_prompt = f"""
You are a function-calling assistant for an apartment rental system. 
You know the following API paths:
1. /apartments
2. /tenancies
3. /persons

- Important: never add filters to function calls. If the user asks for data, return either all results or 
data derivable without using filters. Do not invent SQL clauses or filter conditions.

Rules:
- Only call functions when clearly relevant to the user's request about apartments or rentals.
- If the request is related to the apartment domain but does not require a function 
  (e.g., switching languages, clarifying the question, or guidance), respond naturally.
- Only refuse requests that are completely unrelated to apartments and rentals.
- Always respond in the language requested by the user.
- Always attempt to call the function to get fresh data if relevant.
- If the function returns no data:
    - You may use information from any previous messages in the conversation.
    - **When you do this, prepend your answer with "unverified: " to indicate that this information comes from previous messages and may not be verified.**
- Do not invent data that is not present in either the function results or previous messages.
"""

def ai_generate_query(user_question, func_ai_generate_structured_content):
    """
    AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
    :param func_ai_generate_structured_content: Based on the user's query generates structured data for SQL queries.
    :param user_question: User input to the AI
    :return: JSON data used for a query
    """
    ai_role_prompt = f"""
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
        """
    try:
        # AI moder generates an answer as JSON
        response_json = func_ai_generate_structured_content(ai_role_prompt, user_question)
        return response_json
    except Exception as error:
        print(f"Error generating JSON answer by an AI model: {error}")
        print("Original JSON: ", response_json)
    return None

def execute_restful_api_query_json_param(json_data_for_query) -> dict:
    """
    Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
    :param json_data_for_query: JSON with keys "path" and "filters
    :return: JSON response from the endpoint RESTFUL API
    """
    path = json_data_for_query["path"]

    # list of columns to filter the SQL table
    filters = json_data_for_query.get("filters", [])

    try:
        response = requests.get(path, params=filters)
        response.raise_for_status()  # raises an HTTPError if the server responds with a failed status code.
        return response.json()

    except requests.ConnectionError as error:
        print("Error connecting to the REST API: Flask server is not running.", error)
    except requests.HTTPError as error:
        print(f"Error due returning HTTP error: {error}")
    except Exception as error:
        print(f"Unexpected error calling endpoints by AI: {error}")
    return None

def execute_restful_api_query(path: str, filters: list[str]) -> dict:
    """
    Executes a query from AI to an endpoint RESTFUL API and returns the response.
    :param path: Path to the endpoint RESTFUL API.
    :param filters: Filters to use when executing queries.
    :return: JSON response from the endpoint RESTFUL API.
    """
    try:
        if not path:
            raise ValueError("No path provided")

        url = f"http://{HOST}:{PORT}{path}"
        response = requests.get(url, params=filters)
        response.raise_for_status()  # raises an HTTPError if the server responds with a failed status code.
        return response.json()

    except requests.ConnectionError as error:
        print("Error connecting to the REST API: Flask server is not running.", error)
    except requests.HTTPError as error:
        print(f"Error due returning HTTP error: {error}")
    except ValueError as error:
        print(f"Error due faulty value: {error}")
    except Exception as error:
        print(f"Unexpected error calling endpoints by AI: {error}")
    return None

def ai_represent_answer(restful_api_response, user_question, func_generate_human_like_ai_response):
    """
    Generates a human like answer to a user question using retrieved data from the SQL data bank.
    :param func_generate_human_like_ai_response: The function generates a human like answer to a user question.
    :param restful_api_response: Data from the SQL data bank
    :param user_question: User's question
    :return: Human like text containing an answer to the user's question.
    """
    ai_role_prompt = "You are a helpful assistant."

    if restful_api_response:
        extended_prompt_with_sql = f"""
        User asked: "{user_question}"
        API returned the following data: {restful_api_response}
        Generate a friendly answer to the user based on the real data.
        """
    else:
        extended_prompt_with_sql = f"""
        User asked: "{user_question}"
        The database did not return any useful data for this query.
        Please answer the question as best as you can, without relying on database results.
        """

    # AI answers in a human like message
    response = func_generate_human_like_ai_response(ai_role_prompt, extended_prompt_with_sql)
    return response