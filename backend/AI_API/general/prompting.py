import copy
import json

GET_FUNCTION_CALL_PROMPT = {
  "role": "system",
  "instructions": {
    "purpose": "Decide whether the user's request requires a GET call to the apartment rental REST API.",
    "focus": "Answer only the user's latest request. Use session history only to resolve references; do not restate prior listings unless explicitly asked.",
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
          "If data is missing or incomplete, state 'unverified:' before the corresponding fact instead of guessing.",
          "Do not produce structured JSON to the user — return information only in natural conversational form."
        ]
      },

      "language": {
        "policy": "Respond in the user's language.",
        "tie_breaker": "If the request is mixed-language, use the language of the latest substantive user sentence."
      },

      "unrelated_requests": "If the request is outside the apartment rental domain, respond naturally in free text without JSON or function calls.",
      "missing_fields_policy": "The absence of a specific field in the API schema does not restrict making a GET. Do not invent concrete values. Use the 'unverified:' prefix **only** when a fact is taken from session history (not from the current API result nor from explicit statements in the latest user message), and **only** if neither the API nor the latest user message can answer the request.",
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
  "role": "system",
  "instructions": {
    "task": "Return ONLY a single JSON object with four booleans: {\"create\":bool, \"update\":bool, \"delete\":bool, \"show\":bool}. No prose.",
    "decision_logic": "XOR across C/U/D/SHOW for explicit CRUD/SHOW commands only. If the user asks an informational/analytical question (QA, count, sum, average, compare) without an explicit display verb, then ALL FOUR MUST BE FALSE (handled by the general QA pipeline). Priority if multiple explicit commands: delete > update > create > show.",
    "schema": {
      "create": {"value": "Create/register a NEW record.", "type": "type of record"},
      "update": {"value": "Modify an EXISTING record.", "type": "type of record"},
      "delete": {"value": "Remove/terminate an EXISTING record.", "type": "type of record"},
      "show": {"value": "Explicit UI display command (show/display/list/render/visualize/print/output). Not used for neutral questions like 'how many...'.", "type": "type of record"},
    },
    "examples": [
      {
        "input": "How many apartments?",
        "output": {
          "create": { "value": False, "type": "" },
          "update": { "value": False, "type": "" },
          "delete": { "value": False, "type": "" },
          "show":   { "value": False, "type": "" }
        }
      },
      {
        "input": "Show all apartments in Munich",
        "output": {
          "create": { "value": False, "type": "" },
          "update": { "value": False, "type": "" },
          "delete": { "value": False, "type": "" },
          "show":   { "value": True,  "type": "apartment" }
        }
      },
      {
        "input": "Add a new tenant",
        "output": {
          "create": { "value": True,  "type": "person" },
          "update": { "value": False, "type": "" },
          "delete": { "value": False, "type": "" },
          "show":   { "value": False, "type": "" }
        }
      },
      {
        "input": "Delete contract",
        "output": {
          "create": { "value": False, "type": "" },
          "update": { "value": False, "type": "" },
          "delete": { "value": True,  "type": "rent" },
          "show":   { "value": False, "type": "" }
        }
      }
    ]
  }
}

SHOW_TYPE_CLASSIFIER_PROMPT = {
  "role": "system",
  "instructions": {
    "purpose": "Determine what the user wants to SHOW within the rental domain.",
    "allowed_types": ["apartment", "tenancy", "person", "contract"],

    "rules": [
      "Infer from the user's request what single entity should be shown.",
      "The entity type must be one of: apartment, tenancy, person, contract.",
      "If the request clearly matches an allowed type, return checked: true and that type.",
      "If the request is outside these categories (e.g., cars, stars, unrelated topics), return checked: false and type with the detected (invalid) category.",
      "If the user says 'show' without specifying what, return checked: false and type: \"\" (empty string).",
      "Respond ONLY with one JSON object. No prose outside the JSON."
    ],

    "output_format": "Return JSON: {\"checked\": boolean, \"type\": string, \"message\": string}",

    "message_guidelines": [
      "Write 'message' in the user's language.",
      "Keep it short (1–2 sentences).",
      "For checked=false with empty type → ask the user to choose: apartment, tenancy, person, or contract.",
      "For checked=false with invalid type → say it's not supported and offer the same four choices.",
      "For checked=true → 'message' is a short confirmation."
    ],

    "examples": [
      {"input": "Show me all apartments.",      "output": {"checked": True,  "type": "apartment", "message": "Showing apartments."}},
      {"input": "List all tenants",             "output": {"checked": True,  "type": "person",    "message": "Listing tenants."}},
      {"input": "Display all contracts.",       "output": {"checked": True,  "type": "contract",  "message": "Showing contracts."}},
      {"input": "Show me",                      "output": {"checked": False, "type": "",          "message": "What should I show: apartment, tenancy, person, or contract?"}},
      {"input": "Show me stars in the sky",     "output": {"checked": False, "type": "stars",     "message": "Not supported. Choose: apartment, tenancy, person, or contract."}},
      {"input": "Show me cars in tenant garages","output": {"checked": False, "type": "cars",     "message": "Not supported. Choose: apartment, tenancy, person, or contract."}}
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
      "interpret these phrases only within the short-term context of the last few dialogue turns. "
      "Use the information from your most recent interaction about field collection — not from older parts of the session. "
      "If the user starts describing a new person, object, or entity, treat it as a fresh collection and do not reuse previous data.",

      # Field collection logic
      "At start: show all fields from payload_template to the user (mentioning which are required and which are optional). "
      "Ask explicitly for required_fields first, then offer optional ones.",
      "Treat any later user message as an amendment to fields (even after confirmation). Merge changes, then resummarize collected data.",

      # Readiness conditions
      "Required_fields must be non-empty to become ready. Optional fields can stay empty if the user explicitly says so.",
      "ready_to_post=false until the user gives an explicit, unambiguous confirmation (e.g. 'yes', 'confirm') without new data afterward.",
      "When ready_to_post=true, summarize collected data in 'comment' and state that you are sending them for backend processing (no question).",

      # Language and brevity
      "Keep 'comment' brief and in the user's language. No prose outside JSON.",

      # Cancellation or intent shift
      "If the user clearly cancels or switches intent (e.g. 'cancel', 'show ...'), stop data collection and reflect that in 'comment'."
    ]
  }
}

def inject_fields_to_create_prompt(class_fields, required_fields) -> str:
  """
  Adds dynamically the fields, required for creation an entity (tenant, contract ect).
  :return: Prompt as dict, that contains instruction which fields should be asked by the LLM.
  """
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(CREATE_ENTITY_PROMPT)

  if class_fields:
    combined_prompt["instructions"]["payload_template"] = class_fields

  if required_fields:
      combined_prompt["instructions"]["required_fields"] = required_fields

  system_prompt = json.dumps(combined_prompt, indent=2, ensure_ascii=False)
  return system_prompt


STRUC_OUT_PROMPT= f"""
    You are a structured-output assistant.
    Do not perform or mention any new API calls or endpoints.
    Return ONLY raw JSON (starting with '{{' or '[') representing that data in the required structure.
    
    Rules:
    1. Use exclusively the data explicitly present in the last conversation step.
    2. Do not recall, invent, or infer information from any prior sessions or external sources.
    3. Never generate hypothetical or fabricated data.
    4. If a required field cannot be filled truthfully, output it as `null` or `"no data"`.
    5. If there is no usable data at all, respond only with:
       {{
         "status": "no_data"
       }}
    Your response must remain faithful to the provided conversation state and may never contain imagined values.
"""
