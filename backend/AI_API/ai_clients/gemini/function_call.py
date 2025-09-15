from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting

class FunctionCallService:
    def __init__(self, ai_client: genai.Client, model_name: str):
        """
        Allows the AI model to call functions and then to give to a user a response
        with retrieved data from those functions.
        :param ai_client: AI client
        :param model_name: Name of the used AI model
        """
        self.client = ai_client
        self.model_name = model_name
        # volatile memory of the conversation
        self.session_contents: list[types.Content] = []

        # version of JSON schema for Gemini's function calling
        self.execute_restful_api_query_declaration = {
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
        # tools object, which contains one or more function declarations for function calling by AI.
        tools = types.Tool(function_declarations=[self.execute_restful_api_query_declaration])

        # Configuration for function call and system instructions
        self.config_ai_function_call = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=[types.Part(text=prompting.system_prompt)]
        )

    def get_ai_function_call(self, user_question: str) -> str:
        # get the potential function calling response
        response_candidate = self._order_call_function(user_question)

        fn_call = None
        try:
            # functionCall object in an OpenAPI compatible schema specifying how to call one or
            # more of the declared functions to respond to the question in the prompt.
            fn_call = response_candidate.parts[0].function_call
        except Exception:
            pass

        if fn_call:
            print(f".... AI want to call the function: {fn_call.name} with arguments: {fn_call.args}")
            self._do_call_function(fn_call)

            final_response_content = self._get_ai_response()

            result = FunctionCallService.filter_text_from_ai_response(final_response_content)
            return result

        result = FunctionCallService.filter_text_from_ai_response(response_candidate)
        return result

    def _order_call_function(self, user_question: str) -> genai.types.Content:
        # Add the user prompt to the summary request to AI
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(role="user", parts=[user_part])
        self.session_contents.append(user_part_content)

        # get content of a response with a call function candidate.
        response_call_func_candidate = self._get_ai_response()

        return response_call_func_candidate

    def _get_ai_response(self) -> genai.types.Content:
        ai_response = self.client.models.generate_content(
            model=self.model_name,
            config=self.config_ai_function_call,
            contents=self.session_contents,
        )
        response_content = ai_response.candidates[0].content

        # Place the answer in the conversation history.
        self.session_contents.append(response_content)

        return response_content

    def _do_call_function(self, function_call):
        """
        Calls the function which returns the SQL data.
        Then add the data to the conversation history.
        :param function_call: Object retrieved by the AI model to trigger the function call.
        """
        sql_answer = None
        # Calls the function, to get the data
        if function_call.name == "execute_restful_api_query":
            sql_answer = prompting.execute_restful_api_query(**function_call.args)
            print(".... SQL answer: ", sql_answer)

        # Creates a function response part.
        # Gives the row answer from the called function back to the conversation.
        function_response_part = types.Part.from_function_response(
            name=function_call.name,
            response={"result": sql_answer},
        )

        # Add the actual result of the function execution back into the conversation history,
        # so the model can use it to generate the final response to the user.
        self.session_contents.append(types.Content(role="assistant", parts=[function_response_part]))

    @staticmethod
    def filter_text_from_ai_response(ai_response_content:  genai.types.Content) -> str | None:
        """
        AI response consists of multiple parts. This method filters the non-text part of the response.
        :param ai_response_content: Content response returned by the AI.
        :return: text part of an AI response.
        """
        for part in ai_response_content.parts:
            # part can be text, function_call, thought_signature etc.
            if hasattr(part, "text") and part.text:
                return part.text
        return None