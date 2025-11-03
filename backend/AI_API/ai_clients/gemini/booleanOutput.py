import json

from google import genai
from google.genai import types
import ApartmentManager.backend.AI_API.general.prompting as prompting
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry

class BooleanOutput:
    def __init__(self,
                 llm_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float):
        """
        Service for requesting boolean output from the LLM model.
        """
        self.client = llm_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature

        # Schema as SDK object (used in request config)
        self.schema_boolean = types.Schema(
            title="intent_flags",
            type=types.Type.OBJECT,
            properties={
                "create": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "value": types.Schema(type=types.Type.BOOLEAN),
                        "type": types.Schema(type=types.Type.STRING)
                    }),
                "show": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "value": types.Schema(type=types.Type.BOOLEAN),
                        "type": types.Schema(type=types.Type.STRING)
                    }),
                "update": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "value": types.Schema(type=types.Type.BOOLEAN),
                        "type": types.Schema(type=types.Type.STRING)
                    }),
                "delete": types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "value": types.Schema(type=types.Type.BOOLEAN),
                        "type": types.Schema(type=types.Type.STRING)
                    }),
            },
            required=["create", "show", "update", "delete"]
        )

    def get_boolean_llm_response(self, user_question: str) -> dict | None:
        """
        Requests at LLM a structured response that conforms to the JSON schema.
        Then extracts from the JSON scheme the boolean value.
        Returns boolean value (True or False).
        """
        system_prompt_crud_intent = json.dumps(prompting.CRUD_INTENT_PROMPT, indent=2, ensure_ascii=False)

        # Configuration for the LLM call
        boolean_llm_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=self.schema_boolean,  # SDK object
            temperature=0,  # deterministic behavior, only recognize CRUD intents
            tools=[], # do not use tools, no variations
            system_instruction=types.Part(text=system_prompt_crud_intent)
        )

        try:
            user_content = types.Content(
                role="user",
                parts=[types.Part(text=user_question)]
            )

            llm_answer = self.client.models.generate_content(
                model=self.model,
                contents=[user_content],
                config=boolean_llm_config,
            )
        except ValueError as boolean_error:
            print(ErrorCode.LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE, repr(boolean_error))
            return {
                "type": "error",
                "result": {"message": "Sorry, I couldn’t craft a response this time."},
                "meta": {"model": self.model},
                "error": {"code": ErrorCode.LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE +" :" + repr(boolean_error)}
            }

        try:
            # Scenario 1: SDK has the parsed version of the answer, get it
            llm_answer_crud = getattr(llm_answer, "parsed", None)

            # Scenario 2: SDK does not have the parsed version of the answer
            if llm_answer_crud is None:
                llm_answer_text = llm_answer.candidates[0].content.parts[0].text
                llm_answer_crud = json.loads(llm_answer_text)

        except Exception as parsing_error:
            print(ErrorCode.ERROR_PARSING_BOOLEAN_RESPONSE, repr(parsing_error))
            return {
                "type": "error",
                "result": {"message": "Sorry, I couldn’t craft a response this time."},
                "meta": {"model": self.model},
                "error": {"code": ErrorCode.ERROR_PARSING_BOOLEAN_RESPONSE +" :" + repr(parsing_error)}
            }

        try:
            llm_answer_crud_str = json.dumps(llm_answer_crud, indent=2, ensure_ascii=False, default=str)
            # Add LLM response to log
            create_new_log_entry(
                llm_model=self.model,
                user_question=user_question or "",
                request_type="boolean request",
                backend_response="---",
                llm_answer=llm_answer_crud_str
            )
        except Exception as log_error:
            # Log and return controlled error
            print(ErrorCode.LOG_ERROR_FOR_BOOLEAN_RESPONSE, repr(log_error))

        return llm_answer_crud