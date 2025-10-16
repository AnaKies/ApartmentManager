import copy
import json

GET_FUNCTION_CALL_PROMPT = {
  "role": "system",
  "instructions": {
    "purpose": "Decide whether the user's request requires GET or POST for the apartment rental REST API.",
    "endpoints": ["/apartments", "/tenancies", "/persons", "/rent_data"],

    "rules": {
      "GET": {
        "intent": "retrieve existing data",
        "must": [
          "Use the exact endpoint path with leading slash (e.g., /apartments).",
          "Never add filters, WHERE clauses, or SQL-like conditions.",
          "Return data only directly retrievable from the API.",
          "If the API returns no data, you may recall facts mentioned earlier by the user and prefix them with 'unverified:'."
        ],
        "baseline": True,
        "note": "GET is the default retrieval behavior and must operate without any selectors or trigger words."
      },
      "validation": {
        "confirmation_required": True,
        "missing_fields_prompt": "Ask user only for missing fields.",
        "empty_values": "Represent empty or 'no value' fields as empty string or null.",
        "language": "Respond in the user's language."
      },

      "common": {
        "paths": "Always use the exact endpoint paths with leading slash.",
        "never_both": "Never perform both GET and POST in one message — if such ambiguity appears, choose only one action.",
        "clarify_if_unsure": "If unsure whether GET or POST applies, ask for clarification instead of guessing.",
        "unrelated_requests": "If the request is outside the apartment rental domain, respond naturally and conversationally — not with JSON or refusal message.",
        "no_invention": "Do not modify or invent any data; use only data from the API response or user-provided context."
      }
    },

    "examples": [
      {
        "user": "Show me all apartments.",
        "action": "GET /apartments"
      },
      {
        "user": "List all tenants.",
        "action": "GET /persons"
      }
    ],

    "response_behavior": {
      "format": "natural conversation",
      "preferred_action": "Call GET or POST functions when applicable.",
      "avoid": [
        "guessing missing data",
        "inventing information",
        "returning structured JSON to the user"
      ]
    }
  }
}

# prompting.py

POST_FUNCTION_CALL_PROMPT = {
  "POST": {
    "intent": "create new record",
    "trigger_words": ["add", "create", "insert", "register", "save"],
    "rules": [
      "Perform POST only when the intent to create is clear.",
      "Ask the user only for missing required fields.",
      "Before calling POST, display the JSON payload for confirmation.",
      "Never invent values; use only user-provided fields.",
      "Execute one POST call per turn."
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
    "task": "Return ONLY a single JSON object with four booleans: {\"add\":bool, \"update\":bool, \"delete\":bool, \"show\":bool}. No prose.",
    "decision_logic": "XOR: exactly one of add/update/delete/show must be true; all others false. If intent is unclear → all false. If multiple signals detected, resolve by priority: delete > update > add > show.",
    "schema": {
      "add":   "Create/register/insert/save a NEW record (e.g., new tenant/contract/rent entry).",
      "update":"Modify/edit/correct an EXISTING record’s fields (no new record).",
      "delete":"Remove/terminate/cancel an EXISTING record.",
      "show":  "Display/list/view/retrieve existing data WITHOUT changing it."
    },
    "example": {"add": False, "update": False, "delete": False, "show": True}
  }
}

def combine_get_and_post() -> str:
  """
  Combines prompts for GET and POST tools together.
  :return: Prompt as dict, that contains tools for GET and POST.
  """
  # create a copy and do not touch the oroginals
  combined_prompt = copy.deepcopy(GET_FUNCTION_CALL_PROMPT)

  # Add rules for POST to the level rules
  combined_prompt["instructions"]["rules"]["POST"] = copy.deepcopy(
    POST_FUNCTION_CALL_PROMPT["POST"]
  )

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