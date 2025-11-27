import json
import typing

from ApartmentManager.backend.AI_API.general.envelopes.envelopes_business_logic import DataTypeInDB, \
    ShowOperationData, CrudIntentModel

# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import build_data_answer, AnswerSource, EnvelopeApi
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.rental.CRUD.read import get_persons, get_apartments, get_tenancies, get_contract


def read_action_to_entity(conversation_client: "ConversationClient") -> EnvelopeApi:
    type_to_show = conversation_client.crud_intent_answer.show.type

    result = get_entity_from_db(type_to_show, conversation_client.model_name)

    return result


def get_entity_from_db(data_to_show: DataTypeInDB, model_name: str) -> EnvelopeApi:

    if data_to_show is DataTypeInDB.PERSON:
        db_entities = get_persons()

    elif data_to_show is DataTypeInDB.APARTMENT:
        db_entities = get_apartments()

    elif data_to_show is DataTypeInDB.TENANCY:
        db_entities = get_tenancies()

    elif data_to_show is DataTypeInDB.CONTRACT:
        db_entities = get_contract()

    else:
        trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_SHOW)
        raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_SHOW, trace_id)


    if db_entities:
        payload = [element.to_dict() for element in db_entities]

        result = build_data_answer(payload=payload or {},
                                   payload_comment="Data updated", # it is ok even if the request is SHOW
                                   model=model_name,
                                   answer_source=AnswerSource.BACKEND)

    else:
        trace_id = log_error(ErrorCode.TYPE_ERROR_SHOWING_ENTRY)
        raise APIError(ErrorCode.TYPE_ERROR_SHOWING_ENTRY, trace_id)

    return result