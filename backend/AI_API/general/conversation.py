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
        something_to_show = something_to_show_dict.get("result", False)

        # STEP 2: AI generates an answer with possible function call inside
        answer = self.ai_client.process_function_call_request(user_question)

        if something_to_show:
            answer_str = answer.get("result", {}).get("message", {})

            # Check if SQL returned some data from the database
            if answer_str:
                data_answer = self.ai_client.get_structured_ai_response(user_question)
                return data_answer
        return answer