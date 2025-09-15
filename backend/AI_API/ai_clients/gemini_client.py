import os

import google.genai.types
from google import genai
from google.genai import types
from dotenv import load_dotenv
from google.genai.types import Content

import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.AI_API.general.ai_client import AIClient
from ApartmentManager.backend.AI_API.general.structured_output import response_schema_gemini, QuerySchema

class GeminiClient(AIClient):
    """
    Client implementation for interacting with the Gemini AI model.
    This class provides methods to interface with a RESTful API. It inherits from
    the abstract base class AIClient and implements all required methods.
    """
    # Specify the model to use
    model_name = "gemini-2.5-flash"

    # version of JSON schema for Gemini's function calling
    execute_restful_api_query_declaration = {
        "name": "execute_restful_api_query",
        "description": "Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to an endpoint RESTFUL API",
                },
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Filters to sort the SQL data bank",
                },
            },
            "required": ["path", "filters"],
        },
    }

    def __init__(self):
        # load variables from environment
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=gemini_api_key)

        # tools object, which contains one or more function declarations for function calling by AI.
        tools = types.Tool(function_declarations=[self.execute_restful_api_query_declaration])

        # Configuration for function call and system instructions
        self.config_ai_function_call = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=[types.Part(text=prompting.system_prompt)],
        )

        # volatile memory of the conversation
        self.session_contents: list[types.Content] = []

    def get_ai_function_call(self, user_question: str) -> str:
        # Add the user prompt to the summary request to AI
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(role="user", parts=[user_part])
        self.session_contents.append(user_part_content)

        # The first call of the AI model can return a function call
        ai_response = self.client.models.generate_content(
            model=self.model_name,
            contents=self.session_contents,
            config=self.config_ai_function_call,
        )
        # get content of a response candidate and place it in conversation history
        response_candidate = ai_response.candidates[0].content
        self.session_contents.append(response_candidate)

        fn_call = None
        try:
            # functionCall object in an OpenAPI compatible schema specifying how to call one or
            # more of the declared functions in order to respond to the question in the prompt.
            fn_call = response_candidate.parts[0].function_call
        except Exception:
            pass

        if fn_call:
            print(f".... AI want to call the function: {fn_call.name} with arguments: {fn_call.args}")

            sql_answer = None
            # Calls the function, to get the data
            if fn_call.name == "execute_restful_api_query":
                sql_answer = prompting.execute_restful_api_query(**fn_call.args)
                print(".... SQL answer: ", sql_answer)

            # Creates a function response part.
            # Gives the row answer from the called function back to the conversation.
            # The AI model will combine the initial question with returned data and
            # answer in human like text.
            function_response_part = types.Part.from_function_response(
                name=fn_call.name,
                response={"result": sql_answer},
            )

            # Add the actual result of the function execution back into the conversation history,
            # so the model can use it to generate the final response to the user.
            self.session_contents.append(types.Content(role="assistant", parts=[function_response_part]))

            # The second response from the AI model returns the human like text
            final_response = self.client.models.generate_content(
                model=self.model_name,
                config=self.config_ai_function_call,
                contents=self.session_contents,
            )
            final_response_content = final_response.candidates[0].content
            self.session_contents.append(final_response_content)

            result = GeminiClient.filter_text_from_ai_response(final_response_content)
            return result

        result = GeminiClient.filter_text_from_ai_response(response_candidate)
        return result

    @staticmethod
    def filter_text_from_ai_response(ai_response_content: google.genai.types.Content) -> str:
        """
        AI response consists of multiple parts. This method filters the non-text part of the response.
        :param ai_response_content: Content response returned by the AI.
        :return: text part of an AI response.
        """
        for part in ai_response_content.parts:
            # part can be text, function_call, thought_signature etc.
            if hasattr(part, "text") and part.text:
                return part.text
            else:
                raise ValueError("Error: no text in the AI response!")
        return None

    def get_structured_ai_response(self, ai_role_prompt: str, user_question: str) -> dict:
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

    def get_human_like_ai_response(self, ai_role_prompt: str, user_prompt_with_sql: str) -> str:
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
                                                              self.get_structured_ai_response)
        return generated_query_as_json


    def call_endpoint_restful_api(self, json_data_for_restful_api_request: dict) -> dict:
        """
        Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
        :param json_data_for_restful_api_request: JSON with keys "path" and "filters for a query to an endpoint RESTFUL API.
        :return: JSON response from the endpoint RESTFUL API
        """
        response_json_from_restful_api = prompting.execute_restful_api_query_json_param(json_data_for_restful_api_request)

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
                                                             self.get_human_like_ai_response)
        return human_like_ai_answer