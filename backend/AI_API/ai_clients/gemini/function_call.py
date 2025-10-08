import json
from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.SQL_API.logs.CRUD.create_table_row import create_new_log_entry

class FunctionCallService:
    FUNCTION_TO_CALL = prompting.execute_restful_api_query

    def __init__(self,
                 ai_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float):
        """
        Service that allows the AI model to call functions and then to give to a user a response
        with retrieved data from those functions.
        :param ai_client: AI client
        """
        self.client = ai_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature

        # Converts the Python function into a JSON schema (FunctionDeclaration)
        # so the Gemini client knows this function exists and how to call it.
        self.func_execute_restful_api_query = types.FunctionDeclaration.from_callable(
            callable=self.FUNCTION_TO_CALL,
            client=self.client
        )

        # Tools object, which contains one or more function declarations for function calling by AI.
        tools = types.Tool(function_declarations=[self.func_execute_restful_api_query])

        # Configuration for function call and system instructions
        self.config_ai_function_call = types.GenerateContentConfig(
            tools=[tools],
            temperature=self.temperature, # for stable answers
            system_instruction=types.Part(text=prompting.FUNCTION_CALL_PROMPT)
        )

    def _order_potential_function_call(self, user_question: str) -> genai.types.Content:
        """
        Analyzes the user’s question and proposes a function to retrieve the relevant data.
        :param user_question: Question from the user
        :return: An object containing the information to the function being called
        """
        # Add the user prompt to the summary request to AI
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(
            role="user",
            parts=[user_part]
        )
        self.session_contents.append(user_part_content)

        # get content of a response with a possible call function candidate.
        response_func_candidate = self._get_ai_response()

        return response_func_candidate

    def _get_ai_response(self) -> genai.types.Content:
        """
        The call routine to the AI to retrieve a response.
        The LLM decides if the response is a function call or not.
        :return: Object, containing the information about response
        from the AI (function call object or no)
        """
        ai_response = self.client.models.generate_content(
            model=self.model,
            config=self.config_ai_function_call,
            contents=self.session_contents
        )
        response_content = ai_response.candidates[0].content

        # Place the answer of the AI in the conversation history.
        self.session_contents.append(response_content)

        return response_content

    def _do_call_function(self, function_call_obj) -> dict:
        """
        Calls the function which returns the result data to the AI
        and adds the result data to the conversation history.
        :param function_call_obj: Object retrieved by the AI model to trigger the function call.
        :return: Object containing the SQL data to the AI.
        """
        func_calling_result = None
        # Calls the function, to get the data
        if function_call_obj.name == self.FUNCTION_TO_CALL.__name__:
            func_calling_result = prompting.execute_restful_api_query(**function_call_obj.args)
            print(".... SQL answer: ", func_calling_result)

        # Creates a function response part.
        # Gives the row answer from the called function back to the conversation.
        function_response_part = types.Part.from_function_response(
            name=function_call_obj.name,
            response={"result": func_calling_result},
        )

        # Add the actual result of the function execution back into the conversation history,
        # so the model can use it to generate the final response to the user in the human like form.
        if func_calling_result:
            self.session_contents.append(types.Content(role="assistant", parts=[function_response_part]))

        return func_calling_result


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

    def try_response_using_function_call_data(self, user_question: str) -> dict:
        """
        Gives the user a response using data, retrieved from a function, being called by AI.
        If AI decides not to call the function, the answer of the AI is returned instead.
        :param user_question: Question from the user
        :return: dict with human like text answer containing the information from the function call.
        """
        # STEP 1: get the potential function calling response
        response_func_candidate = self._order_potential_function_call(user_question)

        # Try to extract a function call from the candidate response
        func_call_obj = None
        try:
            # functionCall object in an OpenAPI compatible schema specifying how to call one or
            # more of the declared functions to respond to the question in the prompt.
            func_call_obj = response_func_candidate.parts[0].function_call

        except Exception:
            pass # if no function call, go further, don't throw an exception!!!

        func_calling_result_str = "---"

        if func_call_obj:
            # STEP 2A: the AI model does the function call
            print(f".... AI want to call the function: {func_call_obj.name} with arguments: {func_call_obj.args}")
            try:
                # Execute the function and capture it for later logging
                func_calling_result = self._do_call_function(func_call_obj)
                func_calling_result_str = json.dumps(func_calling_result)
            except Exception as error:
                # If the tool call fails, log the error payload and proceed to get a direct model reply
                func_calling_result_str = json.dumps({"tool_error": str(error)})

            # Ask the model for a final answer using results of the function call,
            # which are saved in the conversation history.
            final_response_content = self._get_ai_response()

            # Extract clean text from the model's final response
            ai_response_text = FunctionCallService._filter_text_from_ai_response(final_response_content)
        else:
            # STEP 2B: No function call. Just extract the direct text answer
            ai_response_text = FunctionCallService._filter_text_from_ai_response(response_func_candidate)

        # STEP 3: Unified logging
        create_new_log_entry(self.model, user_question, func_calling_result_str, ai_response_text)

        # STEP 4: Return envelope
        return {
            "type": "text",
            "result": {
                "function_call": bool(func_call_obj),
                "message": ai_response_text
            },
            "meta": {
                "model": self.model
            }
        }