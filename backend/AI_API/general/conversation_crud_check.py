from __future__ import annotations
import typing
from google.genai import errors as genai_errors
# TYPE_CHECKING import is used to avoid circular imports at runtime.
# At runtime this block is skipped, but type checkers see it and provide
# autocompletion and static type analysis for ConversationClient.
if typing.TYPE_CHECKING:
    from ApartmentManager.backend.AI_API.general.conversation import ConversationClient
from ApartmentManager.backend.AI_API.general.conversation_state import CrudState
from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode
from ApartmentManager.backend.AI_API.general.error_texts import APIError
from ApartmentManager.backend.AI_API.general.logger import log_error

def ai_set_conversation_state(self: "ConversationClient", user_question: str):
    crud_intent_answer = {}
    crud_intent = {}
    try:
        # If one of the CRUD states is active, do not perform the CRUD check
        # Reason: a single CRUD state can consist of multiple conversation-cycles/iterations
        # At the start even the state is None -> the CRUD check is always done at the start

        # Check no active CRUD state (NONE state is active)
        if self.conversation_state.is_none:
            # STEP 1: LLM checks if a user asks for one of CRUD operations
            crud_intent_answer = self.llm_client.get_crud_in_user_question(user_question)
            run_crud_check = True
        else:
            run_crud_check = False

        # actualize the state of the state machine
        if run_crud_check:
            crud_intent = crud_intent_answer or {}
            if (crud_intent.get("create") or {}).get("value"):
                self.conversation_state.set_state(CrudState.CREATE)
            elif (crud_intent.get("update") or {}).get("value"):
                self.conversation_state.set_state(CrudState.UPDATE)
            elif (crud_intent.get("delete") or {}).get("value"):
                self.conversation_state.set_state(CrudState.DELETE)
            elif (crud_intent.get("show") or {}).get("value"):
                self.conversation_state.set_state(CrudState.SHOW)
            else:
                # No explicit CRUD intent detected at the start of a conversation => NONE
                self.conversation_state.set_state(CrudState.NONE)
        # NOTE: if we did NOT run a CRUD check (multi-turn within an active state),
        #       we DO NOT touch the existing ConversationState flags here.

        return crud_intent

    except APIError:
        raise
    # catch a Gemini error
    except genai_errors.APIError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT, error)
        raise APIError(ErrorCode.LLM_ERROR_GETTING_CRUD_RESULT, trace_id) from error