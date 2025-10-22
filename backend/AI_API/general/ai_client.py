from abc import ABC, abstractmethod

class LlmClient(ABC):
    @abstractmethod
    def process_function_call_request(self, user_question: str) -> dict:
        """
        Generates an answer to the users question due retrieving data from the SQL database.
        :param: user_question: The prompt for the user.
        :return: Answer from the LLM model in textual form.
        """

    @abstractmethod
    def get_structured_llm_response(self, user_question: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param: user_question: The prompt for the user.
        :return: JSON representation of the wished data.
        """

    @abstractmethod
    def get_textual_llm_response(self, user_question: str) -> str:
        """
        Generates a human like response to the user's question
        without fetching data from the SQL data bank.
        :param user_question: User's prompt.
        :return: Human like response to the user's question.
        """
