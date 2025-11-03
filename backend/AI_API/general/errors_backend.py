from enum import Enum

# TODO extend an error text to an error number -> find quickly the place in backend where the error was thrown
class ErrorCode(str, Enum):
    LLM_RESPONSE_INTERPRETATION_ERROR = "Failed at interpretation the LLM response."
    LLM_ERROR_GETTING_CRUD_RESULT = "Failed at getting CRUD result."
    LLM_ERROR_COLLECTING_FIELDS_FOR_ENTITY_CREATION = "Failed collecting fields for creation of entity."
    LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW = "Failed collecting types of data to show."
    LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY = "Failed collecting data to create entity."
    LLM_ERROR_DOING_FUNCTION_CALL = "Failed doing function call."
    LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE = "Failed retrieving boolean response."
    LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE = "Failed retrieving structured response."
    LLM_ERROR_GETTING_LLM_ANSWER = "Failed getting LLM answer."
    LLM_ERROR_EMPTY_ANSWER = "Empty LLM answer."

    SQL_ERROR_RETRIEVING_TENANCIES = "Failed retrieving tenancies from SQL database."
    SQL_ERROR_RETRIEVING_CONTRACTS = "Failed retrieving contracts from SQL database."
    SQL_ERROR_RETRIEVING_PERSONS = "Failed retrieving persons from SQL database."
    SQL_ERROR_ADDING_PERSON = "Failed adding person to the SQL database."
    SQL_ERROR_RETRIEVING_APARTMENT = "Failed adding apartment to the SQL database."
    SQL_ERROR_CREATING_NEW_PERSON = "SQL layer did not confirmed the creation of new person."

    ERROR_PARSING_BOOLEAN_RESPONSE = "Failed parsing boolean response."
    ERROR_INJECTING_FIELDS_TO_PROMPT = "Failed injecting fields to prompt."
    LOG_ERROR_FOR_FUNCTION_CALLING = "Error writing log for function calling."
    LOG_ERROR_FOR_BOOLEAN_RESPONSE = "Error writing log for boolean response."
    LOG_ERROR_FOR_STRUCTURED_RESPONSE = "Error writing log for structured response."
    ERROR_CALLING_FUNCTION = "Error calling function."
    ERROR_INTERPRETING_THE_FUNCTION_CALL = "Error interpreting the LLM response."
    ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON = "Error decoding the LLM response."
    ERROR_PERFORMING_CRUD_OPERATION = "Failed performing CRUD operations."
    TYPE_ERROR_CREATING_NEW_ENTRY = "That data type can not be created, because it is not covered in the databank system."

    WARNING_NOT_IMPLEMENTED = "Not implemented."
