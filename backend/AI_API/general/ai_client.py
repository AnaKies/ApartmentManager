from abc import ABC, abstractmethod

class AIClient(ABC):
    @abstractmethod
    def transport_structured_ai_response(self, extended_prompt: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param extended_prompt: User's prompt extended for a command to generate JSON data for the later query.
        :return: JSON scheme containing keywords "path" and "filters for later using in a query.
        """

    @abstractmethod
    def transport_human_like_ai_response(self, extended_prompt: str) -> str:
        """
        Generates a human like response to the user's question using the retrieved data from the SQL data bank.
        :param extended_prompt: User#s prompt extended for retrieved data from the SQL data bank.
        :return: Human like response to the user's question.
        """

    @abstractmethod
    def ai_generate_json_data_for_sql_query(self, user_question: str) -> dict:
        """
        AI add a wrapper to the user prompt and generates JSON data for a query for HTTP requests.
        :param user_question: user input to the AI
        :return: JSON data used for a query
        """

    @abstractmethod
    def call_endpoint_restful_api(self, json_data_for_restful_api_request: dict) -> dict:
        """
        Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.
        :param json_data_for_restful_api_request: JSON with keys "path" and "filters for a query to an endpoint RESTFUL API.
        :return: JSON response from the endpoint RESTFUL API
        """

    @abstractmethod
    def represent_ai_answer(self, restful_api_response: dict, user_question: str) -> str:
        """
        Generates a human like answer to a user question using retrieved data from the SQL data bank.
        :param restful_api_response: Data from the SQL data bank
        :param user_question: User's question
        :return: Human like text containing an answer to the user's question.
        """