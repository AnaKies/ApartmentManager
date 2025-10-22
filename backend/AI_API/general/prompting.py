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

POST_FUNCTION_CALL_PROMPT = {
  "POST": {
    "intent": "create new record",
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

def combine_get_and_post(class_fields: str) -> str:
  """
  Combines prompts for GET and POST tools together.
  :return: Prompt as dict, that contains tools for GET and POST.
  """
  # create a copy and do not touch the originals
  combined_prompt = copy.deepcopy(GET_FUNCTION_CALL_PROMPT)

  combined_prompt["instructions"]["payload_template"] = class_fields
  combined_prompt["instructions"]["guidance_for_payload_template"] = [
    "Use payload_template as the single source of truth for fields to collect.",
    "Do not invent values. Ask the user only for fields that are null or empty.",
    "Echo the payload_template back to the user for confirmation before POST.",
    "Never add fields that are not present in payload_template."
  ]

  # Add rules for POST to the level rules of the GET prompt
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