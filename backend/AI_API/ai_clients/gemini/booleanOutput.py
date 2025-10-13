from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry

class BooleanOutput:
    def __init__(self,
                 ai_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float):
        """
        Service for requesting structured JSON output from the AI model.
        """
        self.client = ai_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature

        # --- 1) Schema as SDK object (used in request config) ---
        # --- Boolean-only Schema ---
        self.schema_boolean = types.Schema(
            title="boolean_response",
            type=types.Type.BOOLEAN
        )

        # Configuration for the AI call
        self.boolean_ai_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=self.schema_boolean,  # SDK object
            temperature=self.temperature,
            system_instruction=types.Part(text=prompting.BOOLEAN_PROMPT)
        )

    def get_boolean_ai_response(self, user_question: str) -> dict | None:
        """
        Requests at AI a structured response that conforms to the JSON schema.
        Then extracts from the JSON scheme the boolean value.
        Returns boolean value (True or False).
        """
        try:
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=user_question)]
            )

            ai_answer = self.client.models.generate_content(
                model=self.model,
                contents=[user_content],
                config=self.boolean_ai_config,
            )
        except ValueError as boolean_error:
            print("Error at boolean AI response", repr(boolean_error))
            return None

        try:
            # Scenario 1: SDK has the parsed version of the answer, get it
            ai_answer_bool = getattr(ai_answer, "parsed", None)

            # Scenario 2: SDK does not have the parsed version of the answer,
            # extract it from the text attribute of the answer object
            if ai_answer_bool is None:
                ai_answer_dirty_str = getattr(ai_answer, "text", "") or ""
                ai_answer_clean_str = ai_answer_dirty_str.strip().lower()
                # Interpret bool from the text string
                if ai_answer_clean_str in ("true", "false"):
                    ai_answer_bool = (ai_answer_clean_str == "true")

            boolean_ai_answer_text = "true" if ai_answer_bool is True else ("false" if ai_answer_bool is False else "")

        except Exception as parsing_error:
            print("Error parsing AI response", repr(parsing_error))
            return None

        # Add AI answer to conversation history
        answer = ai_answer.candidates[0].content
        self.session_contents.append(answer)

        try:
            # Add AI response to log
            create_new_log_entry(
                ai_model=self.model,
                user_question=user_question or "",
                request_type="boolean request",
                backend_response="---",
                ai_answer=boolean_ai_answer_text
            )
        except Exception as log_error:
            # Log and return controlled error so UI can show a modal, not 500
            print("BooleanOutput error:", repr(log_error))
            return None

        return ai_answer_bool