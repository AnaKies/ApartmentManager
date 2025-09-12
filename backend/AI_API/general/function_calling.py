# version of JSON schema for Gemini's function calling
execute_restful_api_query_declaration = {
    "name": "execute_restful_api_query",
    "description": "Execute a query from AI to an endpoint RESTFUL API and return the response from this endpoint.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to an endpoint RESTFUL API",
            },
            "filters": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Filters to sort the SQL data bank",
            },
        },
        "required": ["path", "filters"],
    },
}