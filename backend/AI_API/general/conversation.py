from flask import request, jsonify

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.ai_clients.groq.groq_client import GroqClient

class AiConversationSession:
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
            self.ai_client = GroqClient()
            print("Groq will answer your question.")

    def get_ai_answer(self, user_question):
        """
         JSON-only endpoint for chat.
        :param user_question: { "user_input": "<string>" }
        :return: envelope with type: "text" | "data"
        """

        # structured output for the later implementation of GUI
        if user_question == "show apartments":
            answer_envelope = self.ai_client.process_function_call_request(user_question)
            answer_str = answer_envelope.get("result", {}).get("message", {})
            data_answer = self.ai_client.get_structured_ai_response(answer_str)
            return data_answer

        # Answer of AI with possible function call inside
        answer_human_like = self.ai_client.process_function_call_request(user_question)
        return answer_human_like
