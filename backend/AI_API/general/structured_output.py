from pydantic import BaseModel
from typing import List

class QuerySchema(BaseModel):
    """
    Contract with AI to generate structured output with this JSON schema.
    """
    path: str
    filters: List[str]

# JSON schema for Pydantic / Grok
pedantic_schema = QuerySchema.model_json_schema()

# version of JSON schema for Groq
response_schema_groq = {
    "type": "json_schema",
    "json_schema": {
        "name": "query_schema",
        "schema": QuerySchema.model_json_schema()
    }
}

# version of JSON schema for Gemini's structured output
response_schema_gemini = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "filters": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of columns to filter the SQL table."
        }
    },
    "required": ["path", "filters"]
}