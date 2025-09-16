import ApartmentManager.backend.AI_API.general.prompting as prompting
from google import genai

class StructuredOutput:
    def __init__(self, ai_client: genai.Client, model_name: str):
        """
        Allows the AI model to retrieve an answer as JSON.
        :param ai_client: AI client.
        :param model_name: Model name of an AI client.
        """
        self.client = ai_client
        self.model_name = model_name

        # version of JSON schema for Gemini's structured output
        self.response_schema_gemini = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "area": {"type": "number"},
                    "id_apartment": {"type": "integer"},
                    "price_per_square_meter": {"type": "number"},
                    "utility_billing_provider_id": {"type": "integer"}
                },
                "required": ["address", "area", "id_apartment"]
            }
        }

    def get_structured_ai_response(self, prompt: str) -> dict:
        """
        Generates a structured response according to the given JSON scheme.
        :param: ai_role_prompt: The prompt for the AI behavior.
        :param: user_question: The prompt with user question.
        :return: JSON scheme containing keywords "path" and "filters for later using in a query.
        """
        json_string_for_sql_query = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": self.response_schema_gemini
            }
        )
        # Convert string representation of JSON to dictionary
        dict_for_sql_query = json_string_for_sql_query.parsed
        return dict_for_sql_query