import copy
from enum import Enum
from ApartmentManager.backend.AI_API.general.json_serialisation import dumps_for_llm_prompt
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import EnvelopeApi

GET_FUNCTION_CALL_PROMPT = {
  "role": "system",
  "instructions": {
    "purpose": "Decide whether the user's request requires a GET call to the apartment rental REST API.",
    "focus": "Answer only the user's latest request. Use session history only to resolve references; do not re prior listings unless explicitly asked.",
    "endpoints": ["/apartments", "/tenancies", "/persons", "/rent_data"],

    "rules": {
      "GET": {
        "intent": "Retrieve existing records without modification.",
        "must": [
          "Use only the listed endpoint paths, always starting with a leading slash (e.g., /apartments).",
          "Never modify, filter, or extend endpoint paths.",
          "Return only data that the API can actually retrieve — do not summarize, assume, or interpolate."
        ],
      },

      "data_integrity": {
        "absolute_restrictions": [
          "Never fabricate, infer, or guess information not explicitly provided by the API or user context.",
          "Never alter factual data returned from the API.",
          "Never add speculative fields, invented values, or inferred relationships.",
          "If data is missing or incomplete,  'unverified:' before the corresponding fact instead of guessing.",
          "Do not produce structured JSON to the user — return information only in natural conversational form."
        ]
      },

      "language": {
        "policy": "Respond in the user's language.",
        "tie_breaker": "If the request is mixed-language, use the language of the latest substantive user sentence."
      },

      "unrelated_requests": "If the request is outside the apartment rental domain, respond naturally in free text without JSON or function calls.",
      "missing_fields_policy": "The absence of a specific field in the API schema does not restrict making a GET. Do not invent concrete values. Use the 'unverified:' prefix **only** when a fact is taken from session history (not from the current API result nor from explicit ments in the latest user message), and **only** if neither the API nor the latest user message can answer the request.",
      "verification_policy": "Evidence order when answering: (1) current-turn GET results; (2) session history if it directly answers the request; (3) general domain reasoning per this prompt (no new API calls). Use session history only if needed; when a fact comes from session history, prefix it with 'unverified:'. If none of these provide a basis, say that you cannot verify."
    },

    "examples": [
      {"user": "Show me all apartments.", "action": "GET /apartments"},
      {"user": "List all tenants.", "action": "GET /persons"}
    ],

    "response_behavior": {
      "format": "Always respond in natural conversational text. Never output raw JSON or tool envelopes.",
      "preferred_action": "Call GET only when the user explicitly asks to retrieve existing records for the listed endpoints.",
      "strict_policy": "Never fabricate concrete values for specific records. If a claim cannot be supported by (1) current-turn GET results or (2) session history, you may provide a general-domain answer without asserting verification. Only prefix 'unverified:' when relying on session history. If no basis is available at all, say you cannot verify."
    }
  }
}

POST_FUNCTION_CALL_PROMPT = {
  "POST": {
    "intent": "create new record after explicit confirmation",
    "rules": [
      "Ask for only missing required fields.",
      "Show payload for user confirmation before POST.",
      "Never invent or autofill data.",
      "Execute POST only after explicit confirmation."
    ]
  },

  "examples_post": [
    {
      "user": "Add new tenant Anna Müller with phone number +49123.",
      "action_sequence": [
        "Ask for missing data: bank details, email, comment.",
        "Show payload with all fields.",
        "Ask: 'Confirm to create this record?'",
        "After confirmation → POST /persons"
      ]
    },
    {
      "user": "Create new rent entry for apartment 2, 1000 EUR, paid in June.",
      "action_sequence": [
        "If all required fields are present → show payload.",
        "Ask for confirmation.",
        "After confirmation → POST /rent_data."
      ]
    }
  ]
}

CRUD_INTENT_PROMPT = {
  "feedback": {
    # Injected dynamically by the backend on each turn.
    # Readiness == False → there is an unfinished write-flow (CREATE/UPDATE/DELETE).
    # Readiness == True → no active unfinished write-flow; you may decide intent from the current user input.
    "readiness": True,
    "operation_id": None, # Unique ID of the current operation (if any)

    # The result is an opaque backend payload (for example, an envelope).
    # You MUST NOT use it to decide the current CRUD/SHOW booleans.
    # Its structure is not part of this prompt's contract.
    "result": None,
  },
  "role": "system",
  "instructions": {
    "task": (
      "Return ONLY a single JSON object with four entries: "
      "{\"create\": {\"value\": bool, \"type\": string, \"operation_id\": string}, "
      " \"update\": {\"value\": bool, \"type\": string, \"operation_id\": string}, "
      " \"delete\": {\"value\": bool, \"type\": string, \"operation_id\": string}, "
      " \"show\":   {\"value\": bool, \"type\": string, \"operation_id\": string, \"single\": bool} }. "
      "No prose, no additional keys."
    ),

    "feedback_contract": (
      "The 'feedback' block is provided by the backend:"
      "- feedback.readiness: boolean flag indicating whether the last write-flow "
      "  (CREATE/UPDATE/DELETE) is finished or still ongoing."
      "- feedback.operation_id: a unique identifier for the current operation."
      "- feedback.result: opaque backend payload (for example, an envelope). You MUST NOT use it "
      "  to decide the current CRUD/SHOW booleans, and you MUST NOT assume any specific structure."
    ),

    "state_logic": (
      "Use 'feedback.readiness' and 'feedback.operation_id' as short-term state for an ongoing write-flow (CREATE/UPDATE/DELETE).\n"
      "SHOW is normally stateless and does not depend on this readiness flag."
      "1) If feedback.readiness == false AND feedback.operation_id is NOT None:"
      "   - There is an unfinished write-flow (CREATE/UPDATE/DELETE) identified by operation_id. The last CRUD decision you "
      "     returned in this conversation for that flow is still active."
      "   - You MUST treat ALL user messages as part of this ongoing write-flow, even if they contain verbs like 'update', 'delete', or 'create'."
      "     For example, if the user says 'update comment', and you are in an UPDATE flow, this is a field update, NOT a new intent."
      "   - In that case, you MUST return the SAME CRUD decision (same flag true and same 'type') "
      "     as in your last JSON output."
      "   - IMPORTANT: You MUST include the 'feedback.operation_id' in the 'operation_id' field of the active operation."
      "   - Only if the user explicitly cancels/ends the current operation with clear language "
      "     (for example: 'cancel', 'stop', 'abort', 'forget it'), you may override the previous decision and apply the "
      "     decision_logic for a new operation."

      "2) If feedback.readiness == true:"
      "   - There is no active unfinished write-flow from the backend's perspective."
      "   - You MUST decide CRUD/SHOW intent from the current user input alone, using the decision_logic."
      "   - In this case, set 'operation_id' to empty string \"\" for all operations."

      "3) Never start a new CREATE/UPDATE/DELETE/SHOW operation just because the user provides additional "
      "   data. If the message looks like a follow-up answer ('his name is Max', 'the rent is 900', "
      "   'no parking space', 'IBAN is ...') and feedback.readiness == false, simply reuse your own "
      "   previous CRUD decision."

      "4) If there is an active write-flow (feedback.readiness == false), but the user asks a clearly "
      "   separate informational/analytical question (for example: 'By the way, how many tenants do I "
      "   have in total?'), you may set all four values to false so that the general QA pipeline can "
      "   answer that side question. Do NOT start a new CRUD operation in that case."
    ),

    "decision_logic": (
      "Base CRUD/SHOW detection on explicit user commands and verbs."

      "XOR rule (when deciding a NEW operation):"
      "- At most ONE of create/update/delete/show may have value == true."
      "- Priority if multiple explicit commands are present in the SAME user turn: "
      "  delete > update > create > show."

      "Informational/analytical questions (QA, count, sum, average, compare, reasoning) without an "
      "explicit CRUD/SHOW verb MUST set ALL FOUR values to false, so that the general QA pipeline "
      "handles them."
    ),

    # Minimal semantic hint instead of a heavy schema block
    "schema_hint": (
      "Each key (create, update, delete, show) MUST contain a JSON object with:"
      "- 'value': boolean flag indicating whether this operation is active."
      "- 'type' : free-text string describing the record type (for example: 'person', 'apartment')."
      "- 'operation_id': string, MUST match 'feedback.operation_id' if continuing an operation, otherwise empty string."
      "- 'single': boolean (ONLY for 'show'), true if requesting a specific record, false for list/all."
    ),

    "examples": [
      {
        "input": "How many apartments?",
        "feedback": {
          "readiness": True,
          "result": None
        },
        "output": {
          "create": { "value": False, "type": "person", "operation_id": "" },
          "update": { "value": False, "type": "person", "operation_id": "" },
          "delete": { "value": False, "type": "person", "operation_id": "" },
          "show":   { "value": False, "type": "apartment", "operation_id": "", "single": False }
        }
      },
      {
        "input": "Show all apartments in Munich.",
        "feedback": {
          "readiness": True,
          "result": None
        },
        "output": {
          "create": { "value": False, "type": "person", "operation_id": "" },
          "update": { "value": False, "type": "person", "operation_id": "" },
          "delete": { "value": False, "type": "person", "operation_id": "" },
          "show":   { "value": True,  "type": "apartment", "operation_id": "", "single": False }
        }
      },
      {
        "input": "Add a new tenant.",
        "feedback": {
          "readiness": True,
          "result": None
        },
        "output": {
          "create": { "value": True,  "type": "person", "operation_id": "" },
          "update": { "value": False, "type": "person", "operation_id": "" },
          "delete": { "value": False, "type": "person", "operation_id": "" },
          "show":   { "value": False, "type": "person", "operation_id": "", "single": False }
        }
      },
      {
        "input": "His name is Max Müller.",
        "feedback": {
          "readiness": False,
          "operation_id": "abc12345",
          "result": { "any_backend_state": "ignored_for_intent" }
        },
        "output": {
          "create": { "value": True,  "type": "person", "operation_id": "abc12345" },
          "update": { "value": False, "type": "person", "operation_id": "" },
          "delete": { "value": False, "type": "person", "operation_id": "" },
          "show":   { "value": False, "type": "person", "operation_id": "", "single": False }
        }
      },
      {
        "input": "Delete the current rent contract.",
        "feedback": {
          "readiness": True,
          "result": None
        },
        "output": {
          "create": { "value": False, "type": "person", "operation_id": "" },
          "update": { "value": False, "type": "person", "operation_id": "" },
          "delete": { "value": True,  "type": "contract", "operation_id": "" },
          "show":   { "value": False, "type": "person", "operation_id": "", "single": False }
        }
      }
    ]
  }
}

DELETE_ENTITY_PROMPT = {
  "role": "system",
  "instructions": {
    # Dynamically injected list of valid identifier sets.
    # e.g., [["id"], ["full_name"], ["first_name", "last_name"]]
    "identifier_fields": None,

    "task": (
      "Identify a single entity for deletion using one of the allowed identifier sets. "
      "Respond with a single JSON object: {ready_to_delete: bool, data: object, comment: str}. "
      "Do not perform or mention API calls. Do not delete the record yourself."
    ),

    "principles": [
      # Data Sourcing
      "Use only: (a) payload_template, (b) the user's latest message, and (c) recent dialogue context. Never invent values.",

      # Context reasoning (short-term contextual memory)
      "When reasoning about which identifiers or entities the user refers to (for example, 'that one', 'this person', 'no', 'yes'), "
      "interpret these phrases in the short-term context of the ongoing deletion-identification process. "
      "Pronouns or short answers like 'yes', 'no', 'this one', or 'that one' must be interpreted relative to the assistant's most recent question "
      "about specific identifiers or candidate entities.",

      # Identification Logic
      "Treat 'identifier_fields' as a set of alternative identifier options. Each option is a list of field names that, when all are filled, uniquely identifies one entity.",
      "At the beginning, if no identifier values have been provided yet, briefly explain to the user that there are multiple ways to identify the entity, "
      "based on the options described in 'identifier_fields' (for example, one option may require a single field, another option may require two fields). "
      "Invite the user to choose one of these options.",
      "Once the user starts providing values for one or more fields, infer which identifier option from 'identifier_fields' best matches the fields they are using, "
      "and focus on completing that option.",
      "Collect the minimum data to uniquely identify one person (one complete identifier option), while keeping the data object structurally complete.",
      "The 'data' object must include all field names that appear in any identifier option from 'identifier_fields' (or in payload_template, if provided).",
      "For every field that the user has not filled or that belongs to a non-chosen identifier option, return it with an empty string value \"\".",
      "An entity is considered identified if all fields of at least one identifier option from 'identifier_fields' are filled.",

      # User Interaction
      "If the user's message doesn't provide a valid identifier set, ask for one in the 'comment' (for example, by explaining the available options).",
      "If the user has partially filled one identifier option (for example, provided only one of several fields), ask specifically for the missing fields of that same option.",
      "If conflicting identifiers are given (for example, values that correspond to different identifier options or that are inconsistent), ask for clarification and set ready_to_delete=false.",
      "If a valid identifier option is already complete and the user declines to provide any further details, "
      "keep the existing data object and move toward explicit confirmation instead of treating this as a cancellation.",

      # Dialogue Flow
      "Treat subsequent user messages as updates to the data object. Refresh the 'comment' accordingly.",
      "If the user switches to deleting a new entity, reset the selector and start fresh.",
      "A refusal to add more identifiers or details must NOT be interpreted as a cancellation of the deletion process.",

      # Deletion Readiness
      "Set ready_to_delete=true only after (1) at least one identifier option from 'identifier_fields' is fully collected and (2) the user gives explicit confirmation (e.g., 'yes, delete').",
      "When ready_to_delete=true, the 'comment' should  which entity will be deleted, without asking a question.",

      # Cancellation
      "Treat the deletion process as canceled only if the user clearly expresses that they want to stop or change the task entirely. "
      "In that case, set ready_to_delete=false and  in the 'comment' that the operation was aborted."
    ]
  }
}

# uses the external JSON scheme
CREATE_ENTITY_PROMPT = {
  "role": "system",
  "instructions": {
    "payload_template": None,          # dynamically injected: fields of the entity being created
    "required_fields": None,

    "task": (
      "Collect data for a new entity strictly according to payload_template. "
      "Always respond with ONE JSON object matching the provided JSON Schema "
      "(keys: ready_to_post:boolean, data:object, comment:string). "
      "Do NOT perform or mention any API/tool calls, and do NOT create the record yourself."
    ),

    "principles": [
      # Source of truth
      "Use ONLY: (a) payload_template, (b) the user's latest turn, (c) the context of this dialogue. Never invent values.",

      # Context reasoning (short-term contextual memory)
      "When reasoning about which fields the user refers to (for example, 'leave them empty' or 'add this value'), "
      "interpret these phrases in the short-term context of the ongoing field-collection process. "
      "Pronouns or short answers like 'no' or 'none' must be interpreted relative to the assistant's most recent question "
      "about specific fields (e.g., optional fields). "
      "If the user starts describing a new person, object, or entity, treat it as a fresh collection and do not reuse previous data.",

      # Field collection logic
      "At start: show all fields from payload_template to the user (mentioning which are required and which are optional). "
      "Ask explicitly for required_fields first, then offer optional ones.",
      "Treat any later user message as an amendment to fields (even after confirmation). Merge changes, then resummarize collected data.",

      # New rule – required done, optional skipped
      "If all required_fields are already collected and the user indicates they do not want to fill optional fields "
      "(e.g., 'no', 'none', 'leave them empty', or similar expressions), "
      "the assistant must keep the optional fields empty and proceed toward the confirmation stage, "
      "not treat this as a cancellation of the creation process.",

      # Readiness conditions
      "Required_fields must be non-empty to become ready. Optional fields can stay empty if the user explicitly says so.",
      "ready_to_post=false until the user gives an explicit, unambiguous confirmation (e.g. 'yes', 'confirm') without new data afterward.",
      "When ready_to_post=true, summarize collected data in 'comment' and  that you are sending them for backend processing (no question).",

      # Language and brevity
      "Keep 'comment' brief and in the user's language. No prose outside JSON.",

      # Cancellation or intent shift (slightly softened to avoid misinterpreting 'no' to optional fields)
      "Treat the creation process as canceled only if the user clearly expresses that they want to stop or change the task entirely. "
      "A refusal to fill optional fields must NOT be interpreted as cancellation."
    ]
  }
}

UPDATE_ENTITY_PROMPT = {
  "role": "system",
  "instructions": {
    "payload_template": None,

    "task": (
      "Collect update data for an existing entity strictly according to payload_template. "
      "Return ONE JSON object: {ready:boolean, data:object, comment:string}. "
      "The 'data' object must be a flat dictionary matching ALL keys from payload_template. "
      "Do NOT mention or perform any API/tool calls. Do NOT switch to a 'create new entity' flow."
    ),

    "principles": [

      # Source of truth
      "Use only: (a) payload_template, (b) the user's latest turn, (c) the dialogue context. Never invent values.",

      # Conversation style
      "All wording shown to the user must be natural and human-like. "
      "Do NOT expose internal terms like 'identifier fields', 'options', 'old_first_name', 'old_last_name', "
      "'Option A/B', or phrases such as 'identifier is complete'.",

      # UPDATE flow locking
      "As long as ready=false, you MUST stay inside the UPDATE flow and interpret ALL user messages strictly in the context "
      "of this ongoing update operation, regardless of how short, vague, or ambiguous the user's replies are. "
      "Do NOT switch to any other intent (create, show, delete, general QA) until ready becomes true or the user explicitly "
      "cancels the update task.",

      # STEP 1 — Identify the person
      "First, identify which person the user wants to update. There are three allowed identification options:\n"
      "  • their ID (id_personal_data),\n"
      "  • their last name only,\n"
      "  • their first name AND last name together.\n"
      "In your FIRST identification question you MUST explicitly offer ALL THREE options in one sentence, for example:\n"
      "  'Please tell me their ID, or their last name, or their first and last name, so I can identify the person you want to update.'\n"
      "Only after the user has chosen one of these options may you continue by asking follow-up questions within that chosen option.",
      "Do not use any 'old_' prefixes when talking to the user.",
      "Once one of these options is complete, treat the person as identified and move on to collecting update fields.",
      "If after several clarifications you still cannot reliably identify the person, tell the user that you cannot find a unique match "
      "and explicitly ask them for an ID or a clearer description instead of looping.",

      # STEP 2 — Show and collect update fields
      "After the person is identified, show which fields CAN be updated. "
      "List only the update fields from payload_template (for example: first_name, last_name, bank_data, phone_number, email, comment).",
      "Ask the user which of these fields they want to change and what the new values should be.",
      "If the user writes a short phrase that clearly combines a field name and a value (for example: 'first name Markus', "
      "'last name Müller', 'email test@example.com'), interpret this as BOTH selecting the field AND giving the new value "
      "for that field in the data object.",
      "The user must provide AT LEAST ONE update field. Fields the user does not mention must remain empty string '' in the data object.",
      "If the user corrects or overrides earlier answers, merge changes and provide a brief resummary of the collected updates.",

      # Handling 'no' / 'leave them empty'
      "If the user answers 'no', 'none', 'leave them empty', or 'leave the rest as is' in direct response to a question "
      "about whether they want to update any MORE fields, you MUST interpret this as: "
      "'no additional fields to update in this UPDATE flow'. In that case, if at least one update field is already set, "
      "move to the confirmation step instead of asking for more update fields again.",

      # Readiness, confirmation, and cancellation
      "The JSON field 'ready' must reflect the state of the update flow:\n"
      "- Set ready=false while you are still collecting identifier and/or update fields.\n"
      "- Once a person is identified (by ID, last name, or first+last name) AND at least one update field has a non-empty value, "
      "summarize the planned changes and explicitly ask the user to confirm.\n"
      "- If the user clearly confirms (e.g. 'yes', 'confirm') and no new data is introduced in the same turn, "
      "set ready=true and put a short summary of the update in 'comment'.\n"
      "- If the user clearly refuses at the confirmation stage (e.g. 'no, do not update'), treat this as a cancellation, "
      "set ready=false, and explain briefly in 'comment' that no changes will be applied.",

      # Global cancellation boundary
      "Treat the update process as fully canceled only if the user clearly states that they want to stop or change tasks "
      "(for example: 'stop this', 'forget the update', 'I want to ask something else'). "
      "A simple 'no' or 'leave them empty' in response to questions about additional fields MUST NOT be interpreted as leaving the UPDATE flow.",

      # Language and brevity
      "Keep 'comment' brief and in the user's language. Do not output any text outside the JSON object."
    ]
  }
}


class Prompt(Enum):
  CREATE_ENTITY = CREATE_ENTITY_PROMPT
  UPDATE_ENTITY = UPDATE_ENTITY_PROMPT
  DELETE_ENTITY = DELETE_ENTITY_PROMPT
  CRUD_INTENT = CRUD_INTENT_PROMPT
  GET_FUNCTION_CALL = GET_FUNCTION_CALL_PROMPT
  POST_FUNCTION_CALL = POST_FUNCTION_CALL_PROMPT


def inject_feedback(feedback: (EnvelopeApi, bool), operation_id: str = None):
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(Prompt.CRUD_INTENT.value)

  if feedback:
    combined_prompt["feedback"]["result"] = feedback[0]
    combined_prompt["feedback"]["ready"] = feedback[1]

  if operation_id:
    combined_prompt["feedback"]["operation_id"] = operation_id

  system_prompt = dumps_for_llm_prompt(combined_prompt)

  return system_prompt


def inject_fields_to_delete_in_prompt(fields_combination) -> str:
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(Prompt.DELETE_ENTITY.value)

  if fields_combination:
    combined_prompt["instructions"]["identifier_fields"] = fields_combination

  system_prompt = dumps_for_llm_prompt(combined_prompt)
  return system_prompt


def inject_fields_to_create_in_prompt(class_fields, required_fields) -> str:
  """
  Adds dynamically the fields, required for creation an entity (tenant, contract ect).
  :return: Prompt as dict, that contains instruction which fields should be asked by the LLM.
  """
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(Prompt.CREATE_ENTITY.value)

  if class_fields:
    combined_prompt["instructions"]["payload_template"] = class_fields

  if required_fields:
      combined_prompt["instructions"]["required_fields"] = required_fields

  system_prompt = dumps_for_llm_prompt(combined_prompt)
  return system_prompt


def inject_fields_to_update_in_prompt(class_fields) -> str:
  """
  Adds dynamically the fields, required for creation an entity (tenant, contract ect).
  :return: Prompt as dict, that contains instruction which fields should be asked by the LLM.
  """
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(Prompt.UPDATE_ENTITY.value)

  if class_fields:
    combined_prompt["instructions"]["payload_template"] = class_fields

  system_prompt = dumps_for_llm_prompt(combined_prompt)
  return system_prompt
