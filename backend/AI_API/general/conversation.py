import json

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.ai_clients.groq.groq_client import GroqClient

class AiConversationSession:
    """
    Initializes an AI client and offers methods to open conversation with it.
    """
    def __init__(self, model_choice):
        self.ai_client = None
        model_choice = model_choice

        if model_choice == "Gemini":
            self.ai_client = GeminiClient()
            print("Gemini will answer your question.")
        elif model_choice == "Groq":
            self.ai_client = GroqClient()
            print("Groq will answer your question.")

    def get_ai_answer(self, user_question):
        """
        Depending on the question formulation, this method will return an AI answer
        in human like form or in the form for data representation.
        :param user_question: Question of the user.
        :return: Human-like answer as text or data for data representation as a list of dictionaries
        and a string marking the type of the answer.
        """
        # structured output for the later implementation of GUI
        if user_question == "Show apartments":
            answer_with_apartments = self.ai_client.process_function_call_request(user_question)
            answer_show = self.ai_client.get_structured_ai_response(answer_with_apartments)
            print(type(answer_show))
            return answer_show, "data_answer"

        # Answer of AI with possible function call inside
        answer_human_like = self.ai_client.process_function_call_request(user_question)
        print(type(answer_human_like))
        return answer_human_like, "human_like_answer"