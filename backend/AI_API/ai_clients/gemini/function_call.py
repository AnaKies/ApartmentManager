import json
from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.RESTFUL_API import execute

class FunctionCallService:

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

        # Convert dict to the string with indentation, so that AI can read it better
        self.system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2)

    def _define_potential_function_call(self, user_question: str, system_prompt: str) -> genai.types.Content:
        """
        Retrieves a response from AI with a proposal of function calling.
        Saves the user question to the conversation history.
        :param user_question: Question from the user
        :param system_prompt: Combined system prompt
        :return: An object containing the information to the function being called
        """
        # Add the user prompt to the summary request to AI
        user_part = types.Part(text=user_question)
        user_part_content = types.Content(
            role="user",
            parts=[user_part]
        )
        self.session_contents.append(user_part_content)

        # Function declaration for GET
        func_get = types.FunctionDeclaration.from_callable(
            callable=execute.make_restful_api_get,
            client=self.client
        )

        # Function declaration for POST
        func_post = types.FunctionDeclaration.from_callable(
            callable=execute.make_restful_api_post,
            client=self.client
        )

        # Tools to choose different functions that AI should propose
        get_tool = types.Tool(function_declarations=[func_get])
        post_tool = types.Tool(function_declarations=[func_post])

        # Configuration for function call and system instructions
        config_ai_function_call = types.GenerateContentConfig(
            temperature=self.temperature,  # for stable answers
            system_instruction=system_prompt,
            tools=[get_tool, post_tool]
        )

        # Ask AI to answer the user question with a function calling
        ai_response_with_func_to_call = self.client.models.generate_content(
            model=self.model,
            config=config_ai_function_call,
            contents=self.session_contents
        )
        func_to_call = ai_response_with_func_to_call.candidates[0].content
        # Place the answer of the AI in the conversation history.
        self.session_contents.append(func_to_call)

        return func_to_call


    def _do_call_function(self, function_call_obj) -> dict:
        """
        Calls the function which returns the result data to the AI
        and adds the result data to the conversation history.
        :param function_call_obj: Object retrieved by the AI model to trigger the function call.
        :return: Object containing the SQL data to the AI.
        """
        func_calling_result = None

        # Single-dispatch map by function name (as returned by the model)
        dispatch = {
            execute.make_restful_api_get.__name__: execute.make_restful_api_get,
            execute.make_restful_api_post.__name__: execute.make_restful_api_post,
        }

        func = dispatch.get(function_call_obj.name)
        if func is None:
            print(f"Unknown function requested by AI: {function_call_obj.name}")
        else:
            # Ensure args is a dict before unpacking
            call_args = getattr(function_call_obj, "args", {}) or {}
            func_calling_result = func(**call_args)
            print(".... SQL answer: ", func_calling_result)

        # Creates a function response part.
        # Gives the row answer from the called function.
        # It has to be added to the conversation.
        function_response_part = types.Part.from_function_response(
            name=function_call_obj.name,
            response={"result": func_calling_result},
        )

        # Add the actual result of the function execution back into the conversation history,
        # so the model can use it to generate the final response to the user in the human like form.
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
        if ai_response_content:
            for part in ai_response_content.parts:
                # part can be text, function_call, thought_signature etc.
                if hasattr(part, "text") and part.text:
                    return part.text
        return None

    def try_call_function(self, user_question: str, system_prompt: str) -> dict:
        """
        Gives the user a response using data, retrieved from a function, being called by AI.
        If AI decides not to call the function, the answer of the AI is returned instead.
        :param user_question: Question from the user
        :param system_prompt: Combined system prompt
        :return: dict with function call as string or AI answer as Content.
        """
        # STEP 1: get the potential function calling response
        response_func_candidate = self._define_potential_function_call(user_question, system_prompt)

        # Try to extract a function call from the candidate response
        func_call_obj = None
        try:
            # functionCall object in an OpenAPI compatible schema specifying how to call one or
            # more of the declared functions to respond to the question in the prompt.
            func_call_obj = response_func_candidate.parts[0].function_call

        except Exception:
            pass # if no function call goes further, don't throw an exception!!!

        # STEP 2: the AI model does the function call
        if func_call_obj:
            print(f".... AI want to call the function: {func_call_obj.name} with arguments: {func_call_obj.args}")
            func_calling_result = None
            try:
                # Execute the function with its parameters
                # and save the function call result to the conversation history.
                func_calling_result = self._do_call_function(func_call_obj)

            except Exception as error:
                print("error doing function call by AI: ", error)

            # STEP 3: Return envelope for the AI answers
            # The answer can contain the data from the function call.
            return {
                "type": "data",
                "result": {
                    "function_call": True,
                    "payload": func_calling_result
                },
                "meta": {
                    "model": self.model
                }
            }
        else: # no function call
            # STEP 4a: Return envelope for the AI answer
            # The answer can contain the simple text,
            # as the AI decided to don't call the function.

            ai_answer_without_func_call = FunctionCallService._filter_text_from_ai_response(response_func_candidate)
            return {
                "type": "text",
                "result": {
                    "function_call": False,
                    "message": ai_answer_without_func_call
                },
                "meta": {
                    "model": self.model
                }
            }