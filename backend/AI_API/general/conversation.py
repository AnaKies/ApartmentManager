import json

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry


class AiClient:
    """
    Initializes an AI client and offers methods to open conversation with it.
    """
    def __init__(self, model_choice):
        self.ai_client = None
        self.model = model_choice

        if self.model == "Gemini":
            self.ai_client = GeminiClient()
            print("Gemini will answer your question.")
        elif self.model == "Groq":
            #self.ai_client = GroqClient()
            print("Groq will answer your question.")

    def get_ai_answer(self, user_question) -> dict:
        """
         JSON-only endpoint for chat.
        :param user_question: { "user_input": "<string>" }
        :return: envelope with type: "text" | "data"
        """

        # STEP 1a: AI checks if user asks to add something True/False
        is_request_to_add_data = self.ai_client.add_request_in_user_question(user_question)

        if is_request_to_add_data:


        # STEP 1b: AI checks if user asks to show something True/False
        is_request_to_show_data = self.ai_client.show_request_in_user_question(user_question)

        # STEP 2: AI generates an answer with possible function call inside
        func_call_data_or_ai_text_dict = self.ai_client.process_function_call_request(user_question)

        ai_answer_in_text_format = not func_call_data_or_ai_text_dict.get("result").get("function_call")

        # Scenario 1: AI answered with plain text or raw data should be retrieved
        if ai_answer_in_text_format or is_request_to_show_data:
            # Returns the structured output or
            # a text with reason why the AI decided not to call a function.
            result = func_call_data_or_ai_text_dict

        # Scenario 2: AI answered with function call and this answer should be interpreted
        else:
            # AI is interpreting the data from function call to the human language.
            # Data for the interpretation are taken from the conversation history.
            result = self.ai_client.interpret_ai_response_from_conversation()

        # STEP 3: Unified logging
        ai_answer_str = json.dumps(result, ensure_ascii=False, default=str)
        try:
            func_result = func_call_data_or_ai_text_dict.get("result", {})
            is_func_call = func_result.get("function_call")
            request_type = "function call" if is_func_call else "plain text"
            backend_has_answered = ai_answer_str if is_func_call else "---"

            create_new_log_entry(
                ai_model=self.model,
                user_question=user_question or "---",
                request_type=request_type,
                backend_response=backend_has_answered,
                ai_answer=ai_answer_str
            )
        except Exception as e:
            print("log write failed:", repr(e))

        return result
