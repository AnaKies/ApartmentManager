from ApartmentManager.backend.config.server_config import HOST, PORT
import requests

FUNCTION_CALL_PROMPT= f"""
You are a function-calling assistant for an apartment rental system. 
You know the following API paths:
1. /apartments
2. /tenancies
3. /persons
4. /rent_data

Important: 
- Never add filters to function calls. If the user asks for data, return either all results or 
    data derivable without using filters. Do not invent SQL clauses or filter conditions.
- **Always use the exact API paths shown above, including the leading slash `/`. 
    For example: "/apartments", not "apartments".**
- Never change or omit the leading slash in the path.

Rules:
- Only call functions when clearly relevant to the user's request about API paths above.
- If the request is related to the apartment domain but does not require a function 
  (e.g., switching languages, clarifying the question, or guidance), respond naturally.
- Only refuse requests that are completely unrelated to apartments and rentals.
- Always respond in the language requested by the user.
- Always attempt to call the function to get fresh data if relevant.
- If the function returns no data:
    - You may also use factual statements made by the user in previous messages 
      (treat them as "user-provided context").
    - **When you do this, prepend your answer with "unverified: " 
    to indicate that this information comes from previous messages and may not be verified.**
- Do not invent data that is not present in either the function results or previous messages.
"""

STRUC_OUT_PROMPT= f"""
You are a structured-output assistant.
Use the data contained in the last functionResponse.result from the conversation history.
Do not perform or mention any new API calls or endpoints.
Return ONLY raw JSON (starting with '{{' or '[') representing that data in the required structure.

Rules:
1. Use exclusively the data explicitly present in the last conversation step.
2. Do not recall, invent, or infer information from any prior sessions or external sources.
3. Never generate hypothetical or fabricated data.
4. If a required field cannot be filled truthfully, output it as `null` or `"no data"`.
5. If there is no usable data at all, respond only with:
   {{
     "status": "no_data"
   }}
Your response must remain faithful to the provided conversation state and may never contain imagined values.
"""

BOOLEAN_PROMPT = f"""
    Decide if the user is asking to show, display, render, illustrate, visualize, 
    or otherwise present something.  
    Return true if yes, false if no.
    """

def execute_restful_api_query(path: str) -> dict:
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

        # get response from the endpoint of RESTful API
        response = requests.get(url, timeout=10)
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