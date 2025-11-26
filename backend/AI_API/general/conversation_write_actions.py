import json
import typing

from ApartmentManager.backend.AI_API.general.envelopes.envelopes_business_logic \
    import CrudIntentModel, DataTypeInDB, CollectData
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person
from ApartmentManager.backend.SQL_API.rental.CRUD.delete import delete_person
from ApartmentManager.backend.SQL_API.rental.CRUD.update import update_person
from ApartmentManager.backend.SQL_API.rental.rental_orm_models import PersonalData, Contract, Tenancy, Apartment

# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general import prompting
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import build_text_answer, AnswerSource, \
    EnvelopeApi
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError


def write_action_to_entity(self: "ConversationClient", user_question: str) -> (EnvelopeApi, bool):
    system_prompt = None

    # generates a system prompt with fields injection depending on the CRUD analysis
    if self.crud_intent_data.delete.value:
        system_prompt = generate_prompt_to_delete_entity(self.crud_intent_data)

    elif self.crud_intent_data.create.value:
        system_prompt = generate_prompt_to_create_entity(self.crud_intent_data)

    elif self.crud_intent_data.update.value:
        system_prompt = generate_prompt_to_update_entity(self.crud_intent_data)

    db_entity_data = collect_missing_entity_data(self, user_question, system_prompt)

    envelope_api, ready = call_db_or_collect_missing_data(self, user_question, db_entity_data)

    return envelope_api, ready


def collect_missing_entity_data(self: "ConversationClient", user_question: str, system_prompt: str) -> CollectData:
    # Do the LLM call to collect the additional data for creating an entry
    # and get the user's confirmation for them.
    # Multiple conversation cycles logic.
    db_entity = self.llm_client.write_actions_assistant.do_llm_call(user_question, system_prompt)
    # First, open the standard envelope of the structured output service (result, payload)
    # Inside in the payload there is a custom envelope for entity creation (ready_to_post, data, comment)
    if not db_entity:
        trace_id = log_error(ErrorCode.NO_RESPONSE_FOR_DELETE_OPERATION)
        raise APIError(ErrorCode.NO_RESPONSE_FOR_CREATE_OPERATION, trace_id)

    return db_entity


def call_db_or_collect_missing_data(self: "ConversationClient",
                                    user_question: str,
                                    entity_data: CollectData) -> (EnvelopeApi, bool):
    result = None
    try:
        # Backend calls the SQL layer to delete an entry
        if entity_data.ready:
            # Extract data fields to give them the function
            parsed_args = json.loads(entity_data.data)

            if self.crud_intent_data.delete.value:
                result = remove_entity_from_db(self, parsed_args, user_question)

            elif self.crud_intent_data.create.value:
                result = place_entity_in_db(self, parsed_args, user_question)

            elif self.crud_intent_data.update.value:
                result = update_person_in_db(self, parsed_args, user_question)

            ready = True

        # Wait for new conversation cycle until user provided all data
        # and LLM set the flag ready_to_post.
        # Return the actual comment of the LLM, which should ask for missing data
        else:
            # keep collecting data for creating new entity
            # until the user confirmed the collected data
            result = build_text_answer(message=entity_data.comment,
                                       model=self.model_name,
                                       answer_source=AnswerSource.LLM)
            ready = False

        return result, ready

    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_DELETE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA)
        raise APIError(ErrorCode.ERROR_DELETE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA, trace_id) from error


def remove_entity_from_db(self: "ConversationClient",
                       parsed_args: dict,
                       user_question: str) -> EnvelopeApi:
    result = None
    try:
        type_to_delete = self.crud_intent_data.delete.type

        if type_to_delete is DataTypeInDB.PERSON:
            person = delete_person(**parsed_args)

            # Evaluate entity deletion
            if person:
                result = build_text_answer(message=f"Person {person.first_name or ''} "
                                                   f"{person.last_name or ''} "
                                                   f"with ID {person.id_personal_data}, "
                                                   f"was deleted successfully.",
                                           model=self.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=self.model_name,
                    user_question=user_question or "---",
                    request_type="person deletion",
                    backend_response=str(result),
                    llm_answer="---"
                )

        elif type_to_delete is DataTypeInDB.TENANCY:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_delete is DataTypeInDB.CONTRACT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_delete is DataTypeInDB.APARTMENT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE, trace_id)

        return result

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_REMOVE_ENTITY_FROM_DB)
        raise APIError(ErrorCode.ERROR_REMOVE_ENTITY_FROM_DB, trace_id) from error


def place_entity_in_db(self: "ConversationClient",
                       parsed_args: dict,
                       user_question: str) -> EnvelopeApi:
    result = None

    try:
        type_to_create = self.crud_intent_data.create.type
        if type_to_create is DataTypeInDB.PERSON:
            person_created_data = create_person(**parsed_args)

            # Evaluate new entity creation
            if person_created_data:
                id_person = person_created_data.id_personal_data
                result = build_text_answer(message=f"Person with ID {id_person} "
                                                   f"was created successfully.",
                                           model=self.model_name,
                                           answer_source=AnswerSource.BACKEND)

                create_new_log_entry(
                    llm_model=self.model_name,
                    user_question=user_question or "---",
                    request_type="person creation",
                    backend_response=str(result),
                    llm_answer="---"
                )

        elif type_to_create is DataTypeInDB.TENANCY:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_create is DataTypeInDB.CONTRACT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_create is DataTypeInDB.APARTMENT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_CREATE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_CREATE, trace_id)

        return result

    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_PLACE_ENTITY_TO_DB)
        raise APIError(ErrorCode.ERROR_PLACE_ENTITY_TO_DB, trace_id) from error


def update_person_in_db(self: "ConversationClient",
                          parsed_args: dict,
                          user_question: str) -> EnvelopeApi:
    result = None
    try:
        type_to_update = self.crud_intent_data.update.type

        if type_to_update is DataTypeInDB.PERSON:
            person = update_person(**parsed_args)

            # Evaluate entity deletion
            if person:
                result = build_text_answer(message=f"Person {person.first_name or ''} "
                                                   f"{person.last_name or ''} "
                                                   f"with ID {person.id_personal_data}, "
                                                   f"was updated successfully.",
                                           model=self.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=self.model_name,
                    user_question=user_question or "---",
                    request_type="person updating",
                    backend_response=str(result),
                    llm_answer="---"
                )

        elif type_to_update is DataTypeInDB.TENANCY:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_update is DataTypeInDB.CONTRACT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        elif type_to_update is DataTypeInDB.APARTMENT:
            trace_id = log_error(ErrorCode.WARNING_NOT_IMPLEMENTED)
            raise APIError(ErrorCode.WARNING_NOT_IMPLEMENTED, trace_id)

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE, trace_id)

        return result

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_UPDATE_ENTITY_IN_DB)
        raise APIError(ErrorCode.ERROR_UPDATE_ENTITY_IN_DB, trace_id) from error


def generate_prompt_to_delete_entity(crud_intent: CrudIntentModel) -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param crud_intent: Dictionary containing which CRUD operations that should be done.
    When an operation is "DELETE" = True, then which entity should be created.
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        # Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = crud_intent.delete.type

        if type_of_data is DataTypeInDB.PERSON:
            required_fields = PersonalData.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.CONTRACT:
            required_fields = Contract.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.TENANCY:
            required_fields = Tenancy.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.APARTMENT:
            required_fields = Apartment.required_fields_to_delete_or_update()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY, trace_id)

        if required_fields:
            # Inject the class fields in a prompt
            system_prompt = prompting.inject_fields_to_delete_in_prompt(required_fields)
            json_system_prompt = json.dumps(system_prompt, indent=2, ensure_ascii=False)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_DELETE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_DELETE_PROMPT, trace_id) from error


def generate_prompt_to_create_entity(crud_intent: CrudIntentModel) -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param crud_intent: Dictionary containing which CRUD operations that should be done.
    When an operation is "CREATE" = True, then which entity should be created.
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        #Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = crud_intent.create.type

        if type_of_data is DataTypeInDB.PERSON:
            all_fields = PersonalData.fields_dict()
            required_fields = PersonalData.required_fields_to_create()

        elif type_of_data is DataTypeInDB.CONTRACT:
            all_fields = Contract.fields_dict()
            required_fields = Contract.required_fields_to_create()

        elif type_of_data is DataTypeInDB.TENANCY:
            all_fields = Tenancy.fields_dict()
            required_fields = Tenancy.required_fields_to_create()

        elif type_of_data is DataTypeInDB.APARTMENT:
            all_fields = Apartment.fields_dict()
            required_fields = Apartment.required_fields_to_create()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY, trace_id)

        if all_fields:
            # Inject the class fields in a prompt
            system_prompt = prompting.inject_fields_to_create_in_prompt(all_fields, required_fields)
            json_system_prompt = json.dumps(system_prompt, indent=2, ensure_ascii=False)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_CREATE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_CREATE_PROMPT, trace_id) from error


def generate_prompt_to_update_entity(crud_intent: CrudIntentModel) -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param crud_intent: Dictionary containing which CRUD operations that should be done.
    When an operation is "CREATE" = True, then which entity should be created.
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        #Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = crud_intent.update.type

        if type_of_data is DataTypeInDB.PERSON:
            all_fields = PersonalData.fields_dict()
            required_fields = PersonalData.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.CONTRACT:
            all_fields = Contract.fields_dict()
            required_fields = Contract.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.TENANCY:
            all_fields = Tenancy.fields_dict()
            required_fields = Tenancy.required_fields_to_delete_or_update()

        elif type_of_data is DataTypeInDB.APARTMENT:
            all_fields = Apartment.fields_dict()
            required_fields = Apartment.required_fields_to_delete_or_update()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY, trace_id)

        if all_fields:
            # Inject the class fields in a prompt
            system_prompt = prompting.inject_fields_to_update_in_prompt(all_fields, required_fields)
            json_system_prompt = json.dumps(system_prompt, indent=2, ensure_ascii=False)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_UPDATE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_UPDATE_PROMPT, trace_id) from error