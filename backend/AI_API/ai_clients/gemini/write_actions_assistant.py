import json
import typing

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.ai_clients.gemini.crud_intent_assistant import CrudIntentAssistant
from ApartmentManager.backend.AI_API.ai_clients.gemini.function_call_assistant import FunctionCallAssistant
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_business_logic \
    import get_json_schema, validate_model, CollectData
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error

class WriteActionsAssistant:
    def __init__(self,
                 llm_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float,
                 crud_intent: CrudIntentAssistant,
                 function_call: FunctionCallAssistant):
        """
        Service for requesting structured JSON output from the LLM model.
        """
        self.llm_client = llm_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature
        self.crud_intent = crud_intent
        self.function_call = function_call


    def do_llm_call(self, conversation_client: "ConversationClient", json_schema: dict) -> dict:
        """
        Request a structured response that conforms to the schema.
        :param conversation_client:
        :param json_schema:
        :param system_prompt: Instructions how the LLM model should respond.
        :param user_prompt: Question from the user
        :return:
        """
        try:
            json_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=self.temperature,
                system_instruction=types.Part(text=conversation_client.system_prompt)
            )

            # Add the user prompt to the summary request to LLM
            user_part = types.Part(text=conversation_client.user_question)
            user_part_content = types.Content(
                role="user",
                parts=[user_part]
            )
            self.session_contents.append(user_part_content)

            # get LLM response with possible JSON output
            response_content = self.llm_client.models.generate_content(
                model=self.model,
                config=json_config,
                contents=self.session_contents)

            # Append the model's response to the session history
            if response_content.candidates and response_content.candidates[0].content:
                self.session_contents.append(response_content.candidates[0].content)

            try:
                # Scenario 1: SDK has the parsed version of the answer, get it
                llm_response = getattr(response_content, "parsed", None)

                # Scenario 2: SDK does not have the parsed version of the answer
                if llm_response is None:
                    llm_answer_text = response_content.candidates[0].content.parts[0].text
                    llm_response = json.loads(llm_answer_text)

                return llm_response

            except Exception as error:
                trace_id = log_error(ErrorCode.LLM_ERROR_PARSING_CRUD_ACTION, exception=error)
                raise APIError(ErrorCode.LLM_ERROR_PARSING_CRUD_ACTION, trace_id) from error
        # catch a Gemini error
        except genai_errors.APIError:
            raise
        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_RETRIEVING_STRUCTURED_CRUD_RESPONSE, exception=error)
            raise APIError(ErrorCode.LLM_ERROR_RETRIEVING_STRUCTURED_CRUD_RESPONSE, trace_id) from error
