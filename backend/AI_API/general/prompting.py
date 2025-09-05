from ApartmentManager.backend.config.server_config import HOST, PORT
import requests

def ai_generate_query(user_question, func_ai_generate_structured_content):
    """
    AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
    :param func_ai_generate_structured_content: Based on the user's query generates structured data for SQL queries.
    :param user_question: User input to the AI
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
    try:
        # AI moder generates an answer as JSON
        response_json = func_ai_generate_structured_content(prompt)
        return response_json
    except Exception as error:
        print(f"Error generating JSON answer by an AI model: {error}")
        return None

def execute_restful_api_query(json_data_for_query):
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

def ai_represent_answer(restful_api_response, user_question, generate_human_like_ai_response):
    """
    Generates a human like answer to a user question using retrieved data from the SQL data bank.
    :param generate_human_like_ai_response: Generates a human like answer to a user question.
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
    response = generate_human_like_ai_response(prompt)
    return response