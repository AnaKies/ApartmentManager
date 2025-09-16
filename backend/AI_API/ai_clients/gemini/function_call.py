from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting

class FunctionCallService:
    FUNCTION_TO_CALL = prompting.execute_restful_api_query

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

        # Generates from the method signature a function as JSON
        self.execute_restful_api_query_declaration = types.FunctionDeclaration.from_callable(
            callable=self.FUNCTION_TO_CALL,
            client=self.client
        )

        # tools object, which contains one or more function declarations for function calling by AI.
        tools = types.Tool(function_declarations=[self.execute_restful_api_query_declaration])

        # Configuration for function call and system instructions
        self.config_ai_function_call = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=[types.Part(text=prompting.system_prompt)]
        )

    def response_with_ai_function_call(self, user_question: str) -> str:
        """
        Gives the user a response using data, retrieved from a function, being called by AI.
        :param user_question: Question from the user
        :return: Human like text answer containing the information from the SQL data bank
        """
        # get the potential function calling response
        response_candidate = self._order_function_calling(user_question)

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

            result = FunctionCallService._filter_text_from_ai_response(final_response_content)
            return result

        result = FunctionCallService._filter_text_from_ai_response(response_candidate)
        return result

    def _order_function_calling(self, user_question: str) -> genai.types.Content:
        """
        Analyzes the user’s question and proposes a function to retrieve the relevant data.
        :param user_question: Question from the user
        :return: An object containing the information to the function being called
        """
        # Add the user prompt to the summary request to AI
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(role="user", parts=[user_part])
        self.session_contents.append(user_part_content)

        # get content of a response with a call function candidate.
        response_func_candidate = self._get_ai_response()

        return response_func_candidate

    def _get_ai_response(self) -> genai.types.Content:
        """
        The simple call routine to the AI to retrieve a response.
        :return: Object, containing the information about response from the AI.
        """
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
        Calls the function which returns the SQL data to the AI.
        Then add the data to the conversation history.
        :param function_call: Object retrieved by the AI model to trigger the function call.
        """
        sql_answer = None
        # Calls the function, to get the data
        if function_call.name == self.FUNCTION_TO_CALL.__name__:
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
    def _filter_text_from_ai_response(ai_response_content:  genai.types.Content) -> str | None:
        """
        AI response consists of multiple parts.
        This method filters the non-text part of the response.
        :param ai_response_content: Content response returned by the AI.
        :return: Text part of an AI response.
        """
        for part in ai_response_content.parts:
            # part can be text, function_call, thought_signature etc.
            if hasattr(part, "text") and part.text:
                return part.text
        return None