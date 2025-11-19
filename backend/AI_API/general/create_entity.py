import json
import typing

# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation import ConversationClient
from ApartmentManager.backend.AI_API.general.api_data_type import build_text_answer
from ApartmentManager.backend.AI_API.general.error_texts import APIError, ErrorCode
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.SQL_API.logs.create_log import create_new_log_entry
from ApartmentManager.backend.SQL_API.rental.CRUD.create import create_person


def create_entity_in_db(self: "ConversationClient", user_question: str):

    system_prompt = single_iteration_system_prompt_generation(self)

    # Generate the system prompt only once over the conversation iterations
    if system_prompt:
        self.system_prompt = system_prompt

    payload_struct_output = collect_data_for_entity_creation(self, user_question)

    result = place_entity_in_db_or_collect_missing_data(self, user_question, payload_struct_output)

    return result


def single_iteration_system_prompt_generation(self: "ConversationClient"):
    system_prompt = None

    # Generate the system prompt only once over the conversation iterations
    if self.conversation_state.do_once:
        self.conversation_state.do_once = False

        # Provide an extended system prompt with injected data
        # Generate a new prompt for CREATE operation
        system_prompt = self.llm_client.generate_prompt_to_create_entity(self.crud_intent_data)

    return system_prompt


def collect_data_for_entity_creation(self: "ConversationClient", user_question: str):
    # STEP 2: Do the LLM call to collect the additional data for creating an entry
    # and get the user's confirmation for them.
    # Multiple conversation cycles logic.
    if self.system_prompt:
        response = self.llm_client.process_create_request(user_question, self.system_prompt)
    else:
        trace_id = log_error(ErrorCode.NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_CREATE_OPERATION)
        raise APIError(ErrorCode.NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_CREATE_OPERATION, trace_id)

    # First, open the envelope of the structured output service
    if response:
        result_output = (response or {}).get("result")
        payload_struct_output = (result_output or {}).get("payload")
    else:
        trace_id = log_error(ErrorCode.NO_ACTIVATION_OF_RESPONSE_FOR_CREATE_OPERATION)
        raise APIError(ErrorCode.NO_ACTIVATION_OF_RESPONSE_FOR_CREATE_OPERATION, trace_id)

    return payload_struct_output


def place_entity_in_db_or_collect_missing_data(self: "ConversationClient",
                                               user_question: str,
                                               payload_struct_output: dict):
    # Backend calls the SQL layer to create a new entry
    if (payload_struct_output or {}).get("ready_to_post"):
        # Extract data fields to give them the function
        args = (payload_struct_output or {}).get("data")
        parsed_args = json.loads(args)
        result = place_entity_in_db(self, parsed_args, user_question)

    # Wait for new conversation cycle until user provided all data
    # and LLM set the flag ready_to_post.
    # Return the actual comment of the LLM, which should ask for missing data
    else:
        llm_comment_to_payload = (payload_struct_output or {}).get("comment")

        # keep collecting data for creating new entity
        # until the user confirmed the collected data
        result = build_text_answer(message=llm_comment_to_payload,
                                   model=self.model_name,
                                   answer_source="llm")
    return result

def place_entity_in_db(self: "ConversationClient",
                       parsed_args: dict,
                       user_question: str):
    result = None

    # Back-end calls directly the method to add an entity to SQL databank
    creation_action_data = create_person(**parsed_args)

    # STEP 2: evaluate new entity creation
    if creation_action_data:
        creation_action_flag = (creation_action_data or {}).get("result")

        if creation_action_flag:
            id_person = (creation_action_data or {}).get("person_id")
            result = build_text_answer(message=f"Person with ID {id_person} was created successfully.",
                                       model=self.model_name,
                                       answer_source="backend")
            create_new_log_entry(
                llm_model=self.model_name,
                user_question=user_question or "---",
                request_type="person creation request",
                backend_response=str(result),
                llm_answer="---"
            )
    return result
