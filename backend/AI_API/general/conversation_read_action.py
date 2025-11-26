import json
import typing

from ApartmentManager.backend.AI_API.general.envelopes.envelopes_business_logic import DataTypeInDB, \
    ShowOperationData

# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import build_data_answer, AnswerSource, EnvelopeApi
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract


def read_action_to_entity(self: "ConversationClient") -> EnvelopeApi:
    type_to_show = self.crud_intent_data.show.type

    result = get_entity_from_db(self, type_to_show)

    return result


def get_entity_from_db(self: "ConversationClient", data_to_show: ShowOperationData) -> EnvelopeApi:
    db_entities = None

    # Analyzes what type of data should be shown and does the SQL calls
    if data_to_show.checked:

        if data_to_show.type is DataTypeInDB.PERSON:
            db_entities = get_persons()

        elif data_to_show.type is DataTypeInDB.APARTMENT:
            db_entities = get_apartments()

        elif data_to_show.type is DataTypeInDB.TENANCY:
            db_entities = get_tenancies()

        elif data_to_show.type is DataTypeInDB.CONTRACT:
            db_entities = get_contract()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_SHOW)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_SHOW, trace_id)


    if db_entities:
        payload = [element.to_dict() for element in db_entities]

        result = build_data_answer(payload=payload or {},
                                   payload_comment="Data updated", # it is ok even if the request is SHOW
                                   model=self.llm_client.model_name,
                                   answer_source=AnswerSource.BACKEND)

    else:
        trace_id = log_error(ErrorCode.TYPE_ERROR_SHOWING_ENTRY)
        raise APIError(ErrorCode.TYPE_ERROR_SHOWING_ENTRY, trace_id)

    return result