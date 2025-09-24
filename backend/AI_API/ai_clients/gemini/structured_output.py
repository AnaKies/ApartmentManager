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
        self.model = model_name

        # version of JSON schema for Gemini's structured output
        self.response_schema_gemini = {
            "title": "apartments",
            "type": "array",
            "items": {
                "title": "apartment",
                "type": "object",
                "properties": {
                    "address": {"type": "string", "title": "address"},
                    "area": {"type": "number", "title": "area (m²)"},
                    "id_apartment": {"type": "integer", "title": "apartment ID"},
                    "price_per_square_meter": {"type": "number", "title": "price per square meter"},
                    "utility_billing_provider_id": {"type": "integer", "title": "utility billing provider ID"}
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
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": self.response_schema_gemini
            }
        )
        # Convert string representation of JSON to JSON object
        answer_as_json = json_string_for_sql_query.parsed

        return {
            "type": "data",
            "result": {
                "payload": answer_as_json,
                "schema": self.response_schema_gemini
            },
            "meta": {
                "model": self.model,
            }
        }