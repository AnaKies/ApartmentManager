from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.ai_clients.groq.groq_client import GroqClient

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

    def get_ai_answer(self, user_question) -> str | dict:
        """
         JSON-only endpoint for chat.
        :param user_question: { "user_input": "<string>" }
        :return: envelope with type: "text" | "data"
        """

        # STEP 1: AI checks if user asks to show something True/False
        something_to_show_dict = self.ai_client.get_boolean_answer(user_question)

        if something_to_show_dict:
            something_to_show = something_to_show_dict.get("result", False)
        else:
            something_to_show = False

        # STEP 2: AI generates an answer with possible function call inside
        result_of_func_call = self.ai_client.process_function_call_request(user_question)

        # The data for the interpretation are used from the conversation history
        interpretation_of_func_call = self.ai_client.interpret_ai_response_from_conversation()

        if something_to_show:
            # Check if function call was done
            if (result_of_func_call or {}).get("result").get("function_call"):
                return result_of_func_call
        return interpretation_of_func_call