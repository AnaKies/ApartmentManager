from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting


class BooleanOutput:
    def __init__(self,
                 ai_client: genai.Client,
                 model_name: str,
                 temperature: float):
        """
        Service for requesting structured JSON output from the AI model.
        """
        self.client = ai_client
        self.model = model_name
        self.temperature = temperature

        # --- 1) Schema as SDK object (used in request config) ---
        # --- Boolean-only Schema ---
        self.schema_boolean = types.Schema(
            title="boolean_response",
            type=types.Type.OBJECT,
            properties={
                "result": types.Schema(type=types.Type.BOOLEAN, title="result")
            },
            required=["result"]
        )

    def get_boolean_ai_response(self, prompt: str) -> dict:
        """
        Request a structured response that conforms to the schema.
        Returns boolean response as JSON.
        """

        try:
            # Build proper GenerateContentConfig (no plain dicts here)
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self.schema_boolean,  # SDK object
                temperature=self.temperature,
                system_instruction=types.Part(text=prompting.BOOLEAN_PROMPT)
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

            return payload

        except Exception as e:
            # Log and return controlled error so UI can show a modal, not 500
            print("BooleanOutput error:", repr(e))
            return None