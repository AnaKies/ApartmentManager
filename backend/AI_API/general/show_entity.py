import json
import typing

# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation import ConversationClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.api_data_type import build_data_answer
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract


def show_entity_from_db(self: "ConversationClient", user_question: str):
    # Data preparation
    system_prompt = json.dumps(prompting.SHOW_TYPE_CLASSIFIER_PROMPT, indent=2, ensure_ascii=False)

    # LLM checks if the user provides the data type to show
    prepare_data_to_show = self.llm_client.process_show_request(user_question, system_prompt)

    sql_answer = get_entity_from_db(prepare_data_to_show)

    if sql_answer:
        payload = [element.to_dict() for element in sql_answer]
        self.conversation_state.reset()

        result = build_data_answer(payload=payload or {},
                                   payload_comment="Data updated",
                                   # this text shows the user reaction when the data is shown
                                   model=self.model_name,
                                   answer_source="backend")

    else:
        trace_id = log_error(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY)
        raise APIError(ErrorCode.TYPE_ERROR_CREATING_NEW_ENTRY, trace_id)

    return result


def get_entity_from_db(prepare_data_to_show: dict):
    sql_answer = None

    # Analyzes what type of data should be shown and does the SQL calls
    if ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("checked"):
        data_type_to_show = ((prepare_data_to_show.get("result") or {}).get("payload") or {}).get("type")
        if data_type_to_show == "person":
            sql_answer = get_persons()
        elif data_type_to_show == "apartment":
            sql_answer = get_apartments()
        elif data_type_to_show == "tenancy":
            sql_answer = get_tenancies()
        elif data_type_to_show == "contract":
            sql_answer = get_contract()

    return sql_answer