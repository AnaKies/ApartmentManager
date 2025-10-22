import json

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Contract, Tenancy, Apartment
from ApartmentManager.backend.AI_API.general.errors_backend import ErrorCode

class LlmClient:
    """
    Initializes an LLM client and offers methods to open conversation with it.
    """
    def __init__(self, model_choice):
        self.llm_client = None
        self.model = model_choice

        if self.model == "Gemini":
            self.llm_client = GeminiClient()
            print("Gemini will answer your question.")
        elif self.model == "Groq":
            #self.llm_client = GroqClient()
            print("Groq will answer your question.")

    def get_llm_answer(self, user_question) -> dict:
        """
         JSON-only endpoint for chat.
        :param user_question: { "user_input": "<string>" }
        :return: envelope with type: "text" | "data"
        """
        # Default prompt allows read-only operations (GET)
        system_prompt = json.dumps(prompting.GET_FUNCTION_CALL_PROMPT, indent=2, ensure_ascii=False)

        try:
            # STEP 1b: LLM checks if user asks for one of CRUD operations
            crud_intent = self.llm_client.get_crud_in_user_question(user_question)
        except Exception as error:
            print(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT + " :",repr(error))

        try:
            # Extend the base read-only GET prompt to the POST prompt to add an entry in the SQL table
            if crud_intent.get("create", False).get("value", False):
                type_of_data = crud_intent["create"].get("type", "")
                if type_of_data == "person":
                    class_fields = PersonalData.fields_dict()
                elif type_of_data == "contract":
                    class_fields = Contract.fields_dict()
                elif type_of_data == "tenancy":
                    class_fields = Tenancy.fields_dict()
                elif type_of_data == "apartment":
                    class_fields = Apartment.fields_dict()
                else:
                    class_fields = None

                if class_fields:
                    # Inject the class fields in a prompt
                    system_prompt = prompting.combine_get_and_post(class_fields)
                else:
                    raise Exception("Error: not allowed fields for creating new entry in database.")
        except Exception as error:
            print(ErrorCode.ERROR_INJECTING_FIELDS_TO_PROMPT + " :",repr(error))


        try:
            # STEP 2: LLM generates an answer with possible function call inside
            func_call_data_or_llm_text_dict = self.llm_client.process_function_call_request(user_question,
                                                                                           system_prompt)

            llm_answer_in_text_format = not func_call_data_or_llm_text_dict.get("result").get("function_call")

            something_to_show = crud_intent.get("show", False).get("value", False)
        except Exception as error:
            print(ErrorCode.ERROR_AT_CALLING_FUNCTION + " :", repr(error))

        try:
            # Scenario 1: LLM answered with plain text or raw data should be retrieved
            if llm_answer_in_text_format or something_to_show:
                # Returns the structured output or
                # a text with reason why the LLM decided not to call a function.
                result = func_call_data_or_llm_text_dict

            # Scenario 2: LLM answered with function call and this answer should be interpreted
            else:
                # LLM is interpreting the data from function call to the human language.
                # Data for the interpretation are taken from the conversation history.
                result = self.llm_client.interpret_llm_response_from_conversation()
        except Exception as error:
            print(ErrorCode.ERROR_INTERPRETING_THE_FUNCTION_CALL + " :",repr(error))

        # STEP 3: Unified logging
        llm_answer_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        try:
            func_result = func_call_data_or_llm_text_dict.get("result", {})
            is_func_call = func_result.get("function_call")
            request_type = "function call" if is_func_call else "plain text"

            if is_func_call:
                payload_result = func_result.get("payload")
                payload_result_str = json.dumps(payload_result, indent=2, ensure_ascii=False, default=str)
                backend_response_str = payload_result_str if payload_result_str is not None else "---"
            else:
                backend_response_str = "---"

            create_new_log_entry(
                llm_model=self.model,
                user_question=user_question or "---",
                request_type=request_type,
                backend_response=backend_response_str,
                llm_answer=llm_answer_str
            )
        except Exception as error:
            print(ErrorCode.LOG_ERROR_FOR_FUNCTION_CALLING + " :",repr(error))

        return result
