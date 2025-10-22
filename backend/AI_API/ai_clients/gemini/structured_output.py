import json
from google import genai
from google.genai import types
from ApartmentManager.backend.AI_API.general import prompting
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

    def get_structured_llm_response(self, user_prompt: str) -> dict:
        """
        Request a structured response that conforms to the schema.
        Returns envelope with payload and schema for the frontend.
        :param user_prompt: Question from the user
        :return: dict with JSON-like answer containing the information from the function call.
        """
        llm_response = "---"
        try:
            json_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=self.temperature,
                system_instruction=types.Part(text=prompting.STRUC_OUT_PROMPT)
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

            structured_data = None
            try:
                structured_data = json.loads(llm_response)
                result =  {
                    "type": "data",
                    "result": {
                        "payload": structured_data
                    },
                    "meta": {
                        "model": self.model
                    }
                }
            except json.JSONDecodeError as e:
                print("StructuredOutput error:", repr(e))
                result = {
                    "type": "text",
                    "result": {
                        "message": llm_response
                    },
                    "meta": {
                        "model": self.model
                    },
                    "error": {"code": "STRUCTURED_OUTPUT_FAILED", "message": str(e)}
                }
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
            return result

        except Exception as e:
            # Log and return controlled error so UI can show a modal, not 500
            print("StructuredOutput error:", repr(e))
            return {
                "type": "text",
                "result": {
                    "message": llm_response
                },
                "meta": {
                    "model": self.model
                },
                "error": {"code": "STRUCTURED_OUTPUT_FAILED", "message": str(e)}
            }