import google
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
            # more of the declared functions to respond to the question in the prompt.
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

            result = FunctionCallService.filter_text_from_ai_response(final_response_content)
            return result

        result = FunctionCallService.filter_text_from_ai_response(response_candidate)
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
        return None