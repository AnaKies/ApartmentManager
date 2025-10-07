import json

from google import genai
from google.genai import types

class StructuredOutput:
    def __init__(self, ai_client: genai.Client, model_name: str, session_contents: list):
        """
        Service for requesting structured JSON output from the AI model.
        """
        self.client = ai_client
        self.model = model_name
        self.session_contents = session_contents

        # Schema as SDK object (used in AI request config)
        self.schema_apartments = types.Schema(
            title="apartments",
            type=types.Type.ARRAY,
            items=types.Schema(
                title="apartment",
                type=types.Type.OBJECT,
                properties={
                    "address": types.Schema(type=types.Type.STRING,  title="address"),
                    "area":    types.Schema(type=types.Type.NUMBER,  title="area (m²)"),
                    "id_apartment":              types.Schema(type=types.Type.INTEGER, title="apartment ID"),
                    "price_per_square_meter":    types.Schema(type=types.Type.NUMBER,  title="price per square meter"),
                    "utility_billing_provider_id": types.Schema(type=types.Type.INTEGER, title="utility billing provider ID"),
                },
                required=["address", "area", "id_apartment"],
            )
        )

        # Same schema as dict (returned to frontend)
        self.schema_apartments_json = {
            "title": "apartments",
            "type": "array",
            "items": {
                "title": "apartment",
                "type": "object",
                "properties": {
                    "address": {"type": "string",  "title": "address"},
                    "area":    {"type": "number",  "title": "area (m²)"},
                    "id_apartment":            {"type": "integer", "title": "apartment ID"},
                    "price_per_square_meter":  {"type": "number",  "title": "Eur/m²"},
                    "utility_billing_provider_id": {"type": "integer", "title": "utility billing provider ID"}
                },
                "required": ["address", "area", "id_apartment"]
            }
        }

    def get_structured_ai_response(self, user_prompt: str) -> dict:
        """
        Request a structured response that conforms to the schema.
        Returns envelope with payload and schema for the frontend.
        :param user_prompt: Question from the user
        :return: dict with JSON-like answer containing the information from the function call.
        """
        try:
            json_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.schema_apartments,  # SDK object
            )

            # Add the user prompt to the summary request to AI
            user_part = types.Part(text=user_prompt)
            user_part_content = types.Content(
                role="user",
                parts=[user_part]
            )
            self.session_contents.append(user_part_content)

            # get AI response with possible JSON output
            response = self.client.models.generate_content(
                model=self.model,
                config=json_config,
                contents=self.session_contents
            )

            response_content = response.candidates[0].content
            text = response_content.parts[0].text

            try:
                structured_data = json.loads(text)
            except json.JSONDecodeError:
                structured_data = None  # model answered with text, not with JSON

            return {
                "type": "data",
                "result": {
                    "payload": structured_data,
                    "schema": self.schema_apartments_json   # dict for UI with titles
                },
                "meta": {"model": self.model}
            }

        except Exception as e:
            # Log and return controlled error so UI can show a modal, not 500
            print("StructuredOutput error:", repr(e))
            return {
                "type": "data",
                "result": {
                    "payload": None,
                    "schema": self.schema_apartments_json
                },
                "meta": {"model": self.model},
                "error": {"code": "STRUCTURED_OUTPUT_FAILED", "message": str(e)}
            }