import inspect
import typing
from ApartmentManager.backend.AI_API.general.json_serialisation import dumps_for_llm_prompt
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_business_logic \
    import CrudIntentModel, DataTypeInDB, CollectData, get_json_schema, validate_model
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.AI_API.general.prompting import Prompt
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person, create_apartment, create_tenancy, create_contract
from ApartmentManager.backend.SQL_API.rental.CRUD.delete import delete_person, delete_apartment, delete_tenancy, delete_contract
from ApartmentManager.backend.SQL_API.rental.CRUD.update import update_person, update_apartment, update_tenancy, update_contract
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


def write_action_to_entity(conversation_client: "ConversationClient") -> (EnvelopeApi, bool):
    # generates a system prompt with fields injection depending on the CRUD analysis
    if conversation_client.crud_intent_answer.delete.value:
        conversation_client.system_prompt = generate_prompt_to_delete_entity(conversation_client)

    elif conversation_client.crud_intent_answer.create.value:
        conversation_client.system_prompt = generate_prompt_to_create_entity(conversation_client)

    elif conversation_client.crud_intent_answer.update.value:
        conversation_client.system_prompt = generate_prompt_to_update_entity(conversation_client)

    db_entity_data = collect_missing_entity_data(conversation_client)
    envelope_api, ready = call_db_or_collect_missing_data(conversation_client, db_entity_data)

    return envelope_api, ready


def collect_missing_entity_data(conversation_client: "ConversationClient") -> CollectData:
    # Do the LLM call to collect the additional data for creating an entry
    # and get the user's confirmation for them.
    # Multiple conversation cycles logic.
    json_schema = get_json_schema(CollectData)
    db_entity_dict = conversation_client.llm_client.write_actions_assistant.do_llm_call(conversation_client, json_schema)
    db_entity = validate_model(CollectData, db_entity_dict)
    # First, open the standard envelope of the structured output service (result, payload)
    # Inside in the payload there is a custom envelope for entity creation (ready_to_post, data, comment)
    if not db_entity:
        trace_id = log_error(ErrorCode.NO_RESPONSE_FOR_DELETE_OPERATION)
        raise APIError(ErrorCode.NO_RESPONSE_FOR_CREATE_OPERATION, trace_id)

    return db_entity


def call_db_or_collect_missing_data(conversation_client: "ConversationClient",
                                    entity_data: CollectData) -> (EnvelopeApi, bool):
    result = None
    try:
        # Backend calls the SQL layer to delete an entry
        if entity_data.ready:
            # Extract data fields to give them the function
            if entity_data.data:
                parsed_args = entity_data.data.model_dump()
            else:
                parsed_args = {}

            if conversation_client.crud_intent_answer.delete.value:
                result = remove_entity_from_db(conversation_client, parsed_args)

            elif conversation_client.crud_intent_answer.create.value:
                result = place_entity_in_db(conversation_client, parsed_args)

            elif conversation_client.crud_intent_answer.update.value:
                result = update_entity_in_db(conversation_client, parsed_args)

            ready = True

            create_new_log_entry(
                llm_model=conversation_client.model_name,
                user_question=conversation_client.user_question or "---",
                backend_response="---",
                llm_answer=result.model_dump_json(),
                system_prompt_name=conversation_client.system_prompt_name
            )

        # Wait for new conversation cycle until user provided all data
        # and LLM set the flag ready_to_post.
        # Return the actual comment of the LLM, which should ask for missing data
        else:
            # keep collecting data for creating new entity
            # until the user confirmed the collected data
            result = build_text_answer(message=entity_data.comment,
                                       model=conversation_client.model_name,
                                       answer_source=AnswerSource.LLM)
            ready = False

            create_new_log_entry(
                llm_model=conversation_client.model_name,
                user_question=conversation_client.user_question or "---",
                backend_response="---",
                llm_answer=result.model_dump_json(),
                system_prompt_name=conversation_client.system_prompt_name
            )

        return result, ready
    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_DELETE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA, exception=error)
        raise APIError(ErrorCode.ERROR_DELETE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA, trace_id) from error


def remove_entity_from_db(conversation_client: "ConversationClient",
                            parsed_args: dict) -> EnvelopeApi:
    result = None
    try:
        type_to_delete = conversation_client.crud_intent_answer.delete.type

        if type_to_delete is DataTypeInDB.PERSON:
            valid_keys = inspect.signature(delete_person).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            person = delete_person(**filtered_args)
            first_name = person.get("first_name" or "")
            last_name = person.get("last_name" or "")
            id_person = person.get("id_personal_data" or "")

            # Evaluate entity deletion
            if person:
                result = build_text_answer(message=f"Person {first_name or ''} "
                                                   f"{last_name or ''} "
                                                   f"with ID {id_person}, "
                                                   f"was deleted successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_delete is DataTypeInDB.TENANCY:
            valid_keys = inspect.signature(delete_tenancy).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            tenancy = delete_tenancy(**filtered_args)
            id_tenancy = tenancy.get("id_tenancy")

            if tenancy:
                result = build_text_answer(message=f"Tenancy with ID {id_tenancy} was deleted successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_delete is DataTypeInDB.CONTRACT:
            valid_keys = inspect.signature(delete_contract).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            contract = delete_contract(**filtered_args)
            id_contract = contract.get("id_contract")

            if contract:
                result = build_text_answer(message=f"Contract with ID {id_contract} was deleted successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_delete is DataTypeInDB.APARTMENT:
            valid_keys = inspect.signature(delete_apartment).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            apartment = delete_apartment(**filtered_args)
            id_apartment = apartment.get("id_apartment")
            address = apartment.get("address")

            if apartment:
                result = build_text_answer(message=f"Apartment at {address} with ID {id_apartment} was deleted successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE, trace_id)

        return result

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_REMOVE_ENTITY_FROM_DB, exception=error)
        raise APIError(ErrorCode.ERROR_REMOVE_ENTITY_FROM_DB, trace_id) from error


def place_entity_in_db(conversation_client: "ConversationClient",
                       parsed_args: dict) -> EnvelopeApi:
    result = None

    try:
        type_to_create = conversation_client.crud_intent_answer.create.type
        if type_to_create is DataTypeInDB.PERSON:
            valid_keys = inspect.signature(create_person).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            person_created_data = create_person(**filtered_args)

            # Evaluate new entity creation
            if person_created_data:
                first_name = person_created_data.get("first_name") or ""
                last_name = person_created_data.get("last_name") or ""
                id_person = person_created_data.get("id_personal_data") or 0

                result = build_text_answer(message=f"Person {first_name} {last_name} with ID {id_person} "
                                                   f"was created successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)

                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_create is DataTypeInDB.TENANCY:
            valid_keys = inspect.signature(create_tenancy).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            tenancy_created_data = create_tenancy(**filtered_args)

            if tenancy_created_data:
                id_tenancy = tenancy_created_data.get("id_tenancy")
                result = build_text_answer(message=f"Tenancy with ID {id_tenancy} was created successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_create is DataTypeInDB.CONTRACT:
            valid_keys = inspect.signature(create_contract).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            contract_created_data = create_contract(**filtered_args)

            if contract_created_data:
                id_contract = contract_created_data.get("id_contract")
                result = build_text_answer(message=f"Contract with ID {id_contract} was created successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        elif type_to_create is DataTypeInDB.APARTMENT:
            valid_keys = inspect.signature(create_apartment).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            apartment_created_data = create_apartment(**filtered_args)

            if apartment_created_data:
                id_apartment = apartment_created_data.get("id_apartment")
                address = apartment_created_data.get("address")
                result = build_text_answer(message=f"Apartment at {address} with ID {id_apartment} was created successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name
                )

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_CREATE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_CREATE, trace_id)

        return result

    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_PLACE_ENTITY_TO_DB, exception=error)
        raise APIError(ErrorCode.ERROR_PLACE_ENTITY_TO_DB, trace_id) from error


def update_entity_in_db(conversation_client: "ConversationClient",
                        parsed_args: dict) -> EnvelopeApi:
    result = None
    try:
        type_to_update = conversation_client.crud_intent_answer.update.type

        if type_to_update is DataTypeInDB.PERSON:
            valid_keys = inspect.signature(update_person).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            person = update_person(**filtered_args)

            # Evaluate entity update
            if person:
                first_name = person.get("first_name") or ""
                last_name = person.get("last_name") or ""
                id_person = person.get("id_personal_data") or 0

                result = build_text_answer(message=f"Person {first_name or ''} "
                                                   f"{last_name or ''} "
                                                   f"with ID {id_person}, "
                                                   f"was updated successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name)

        elif type_to_update is DataTypeInDB.TENANCY:
            valid_keys = inspect.signature(update_tenancy).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            tenancy = update_tenancy(**filtered_args)
            id_tenancy = tenancy.get("id_tenancy")

            if tenancy:
                result = build_text_answer(message=f"Tenancy with ID {id_tenancy} was updated successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name)

        elif type_to_update is DataTypeInDB.CONTRACT:
            valid_keys = inspect.signature(update_contract).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            contract = update_contract(**filtered_args)
            id_contract = contract.get("id_contract")

            if contract:
                result = build_text_answer(message=f"Contract with ID {id_contract} was updated successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name)

        elif type_to_update is DataTypeInDB.APARTMENT:
            valid_keys = inspect.signature(update_apartment).parameters.keys()
            filtered_args = {k: v for k, v in parsed_args.items() if k in valid_keys}
            apartment = update_apartment(**filtered_args)
            id_apartment = apartment.get("id_apartment")
            address = apartment.get("address")

            if apartment:
                result = build_text_answer(message=f"Apartment at {address} with ID {id_apartment} was updated successfully.",
                                           model=conversation_client.model_name,
                                           answer_source=AnswerSource.BACKEND)
                create_new_log_entry(
                    llm_model=conversation_client.model_name,
                    user_question=conversation_client.user_question or "---",
                    backend_response=result.model_dump_json(),
                    llm_answer="---",
                    system_prompt_name=conversation_client.system_prompt_name)

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_TO_CHECK_ENTITY_TO_DELETE, trace_id)

        return result

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_UPDATE_ENTITY_IN_DB, exception=error)
        raise APIError(ErrorCode.ERROR_UPDATE_ENTITY_IN_DB, trace_id) from error


def generate_prompt_to_delete_entity(conversation_client: "ConversationClient") -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param conversation_client:
    :param crud_intent: Dictionary containing which CRUD operations that should be done.
    When an operation is "DELETE" = True, then which entity should be created.
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        # Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = conversation_client.crud_intent_answer.delete.type

        if type_of_data is DataTypeInDB.PERSON:
            required_fields = PersonalData.required_fields_to_delete()

        elif type_of_data is DataTypeInDB.CONTRACT:
            required_fields = Contract.required_fields_to_delete()

        elif type_of_data is DataTypeInDB.TENANCY:
            required_fields = Tenancy.required_fields_to_delete()

        elif type_of_data is DataTypeInDB.APARTMENT:
            required_fields = Apartment.required_fields_to_delete()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY, trace_id)

        if required_fields:
            # Inject the class fields in a prompt
            system_prompt = prompting.inject_fields_to_delete_in_prompt(required_fields)
            conversation_client.system_prompt_name = Prompt.DELETE_ENTITY.name

            json_system_prompt = dumps_for_llm_prompt(system_prompt)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_DELETE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_DELETE_PROMPT, trace_id) from error


def generate_prompt_to_create_entity(conversation_client: "ConversationClient") -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param conversation_client:
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        #Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = conversation_client.crud_intent_answer.create.type

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
            conversation_client.system_prompt_name = Prompt.CREATE_ENTITY.name

            json_system_prompt = dumps_for_llm_prompt(system_prompt)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_CREATE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_CREATE_PROMPT, trace_id) from error


def generate_prompt_to_update_entity(conversation_client: "ConversationClient") -> str | None:
    """
    Analyzes the CRUD intent for creation of an entity (person, contract ect.)
    and generates a system prompt containing dynamic fields for an entity.
    :param conversation_client:
    :return: System prompt extended with fields
    """
    json_system_prompt = None
    try:
        #Analyze the CRUD intention and inject appropriates fields into the prompt for CREATE operation
        type_of_data = conversation_client.crud_intent_answer.update.type

        if type_of_data is DataTypeInDB.PERSON:
            all_fields = PersonalData.fields_dict_for_update()

        elif type_of_data is DataTypeInDB.CONTRACT:
            all_fields = Contract.fields_dict_for_update()

        elif type_of_data is DataTypeInDB.TENANCY:
            all_fields = Tenancy.fields_dict_for_update()

        elif type_of_data is DataTypeInDB.APARTMENT:
            all_fields = Apartment.fields_dict_for_update()

        else:
            trace_id = log_error(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY)
            raise APIError(ErrorCode.NOT_ALLOWED_NAME_FOR_ENTITY, trace_id)

        if all_fields:
            # Inject the class fields in a prompt
            system_prompt = prompting.inject_fields_to_update_in_prompt(all_fields)
            conversation_client.system_prompt_name = Prompt.UPDATE_ENTITY.name

            json_system_prompt = dumps_for_llm_prompt(system_prompt)
        return json_system_prompt

    except APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_INJECTING_FIELDS_TO_UPDATE_PROMPT, exception=error)
        raise APIError(ErrorCode.ERROR_INJECTING_FIELDS_TO_UPDATE_PROMPT, trace_id) from error