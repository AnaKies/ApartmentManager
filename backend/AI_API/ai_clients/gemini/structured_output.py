import json
from google import genai
from google.genai import types

from ApartmentManager.backend.AI_API.general.api_data_type import build_data_answer
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry

class StructuredOutput:
    def __init__(self,
                 llm_client: genai.Client,
                 model_name: str,
                 session_contents: list,
                 temperature: float):
        """
        Service for requesting structured JSON output from the LLM model.
        """
        self.client = llm_client
        self.model = model_name
        self.session_contents = session_contents
        self.temperature = temperature

    def get_structured_llm_response(self, user_prompt: str,
                                    system_prompt: str,
                                    json_schema: types.Schema) -> dict:
        """
        Request a structured response that conforms to the schema.
        :param system_prompt: Instructions how the LLM model should respond.
        :param json_schema: Scheme for the LLM structured response.
        :param user_prompt: Question from the user
        :return: Envelope-dictionary with answer as payload of the envelope.
        The payload is in JSON format corresponded to the given scheme.
        """
        llm_response = None
        try:
            json_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=self.temperature,
                system_instruction=types.Part(text=system_prompt)
            )

            # Add the user prompt to the summary request to LLM
            user_part = types.Part(text=user_prompt)
            user_part_content = types.Content(
                role="user",
                parts=[user_part]
            )
            self.session_contents.append(user_part_content)

            # get LLM response with possible JSON output
            response = self.client.models.generate_content(
                model=self.model,
                config=json_config,
                contents=self.session_contents
            )

            response_content = response.candidates[0].content
            llm_response = response_content.parts[0].text

        except Exception as error:
            trace_id = log_error(ErrorCode.LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE, exception=error)
            raise APIError(ErrorCode.LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE, trace_id)

        try:
            structured_data = json.loads(llm_response)

            result = build_data_answer(payload=structured_data or {},
                                       payload_comment="-",
                                       model=self.model,
                                       answer_source="llm")
        except json.JSONDecodeError as error:
            trace_id = log_error(ErrorCode.ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON, exception=error)
            raise APIError(ErrorCode.ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON, trace_id)

        try:
            # Add AI answer to logs
            if structured_data:
                struct_output_str = json.dumps(structured_data, ensure_ascii=False)
            else:
                struct_output_str = "no structured AI answer"

            create_new_log_entry(
                llm_model=self.model,
                user_question=user_prompt or "",
                request_type="structured output request",
                backend_response="---",
                llm_answer=struct_output_str
            )
        except Exception as error:
            trace_id = log_error(ErrorCode.LOG_ERROR_FOR_STRUCTURED_RESPONSE, exception=error)
            raise APIError(ErrorCode.LOG_ERROR_FOR_STRUCTURED_RESPONSE, trace_id)

        return result