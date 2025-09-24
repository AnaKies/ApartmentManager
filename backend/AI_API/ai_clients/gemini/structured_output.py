import ApartmentManager.backend.AI_API.general.prompting as prompting
from google import genai
from google.genai import types

class StructuredOutput:
    def __init__(self, ai_client: genai.Client, model_name: str):
        """
        Service for requesting structured JSON output from the AI model.
        """
        self.client = ai_client
        self.model = model_name

        # --- 1) Schema as SDK object (used in request config) ---
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

        # --- 2) Same schema as plain dict (returned to frontend) ---
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
                    "price_per_square_meter":  {"type": "number",  "title": "price per square meter"},
                    "utility_billing_provider_id": {"type": "integer", "title": "utility billing provider ID"}
                },
                "required": ["address", "area", "id_apartment"]
            }
        }

    def get_structured_ai_response(self, prompt: str) -> dict:
        """
        Request a structured response that conforms to the schema.
        Returns envelope with payload + schema for the frontend.
        """
        
        try:
            # Build proper GenerateContentConfig (no plain dicts here)
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.schema_apartments,  # SDK object
            )

            user_content = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )

            resp = self.client.models.generate_content(
                model=self.model,
                contents=[user_content],
                config=gen_config,
            )

            # Prefer parsed Python structure; fallback to raw text
            payload = resp.parsed if getattr(resp, "parsed", None) is not None else resp.text

            return {
                "type": "data",
                "result": {
                    "payload": payload,
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