from enum import Enum

class APIError(Exception):
    def __init__(self, error_code_obj, trace_id=None):
        # Extract a code and message from the enum ErrorCode
        error_code, error_message = error_code_obj.value
        self.error_code = error_code or None
        self.message = error_message or "-"
        self.trace_id = trace_id or "-"

        # The error mechanism of python will show this text in the error
        super().__init__(f"APIError {self.error_code}: {self.message} (trace_id={self.trace_id})")

    def __str__(self):
        return (f"APIError {self.error_code}: {self.message} "
                f"(trace_id={self.trace_id}). ")

    def __repr__(self):
        return (f"APIError {self.error_code}: {self.message} "
                f"(trace_id={self.trace_id}). ")

class ErrorCode(Enum):
    # LLM
    LLM_RESPONSE_INTERPRETATION_ERROR = (1001, "Failed at interpretation the LLM response.")
    LLM_ERROR_GETTING_CRUD_RESULT = (1002, "Failed at getting CRUD result.")
    LLM_ERROR_COLLECTING_TYPE_OF_DATA_TO_SHOW = (1004, "Failed collecting types of data to show.")
    LLM_ERROR_COLLECTING_DATA_TO_CREATE_ENTITY = (1005, "Failed collecting data to create entity.")
    LLM_ERROR_DOING_FUNCTION_CALL = (1006, "Failed doing function call.")
    LLM_ERROR_CALLING_FUNCTION_PROPOSED_BY_LLM = (1009, "Failed calling function proposed by LLM.")
    LLM_ERROR_RETRIEVING_BOOLEAN_RESPONSE = (1007, "Failed retrieving boolean response.")
    LLM_ERROR_RETRIEVING_STRUCTURED_RESPONSE = (1008, "Failed retrieving structured response.")
    LLM_ERROR_EMPTY_ANSWER = (1010, "Empty LLM answer.")
    LLM_ERROR_NO_TEXT_ANSWER = (1011, "LLM does not have a text answer.")

    # SQL error
    SQL_ERROR_DELETING_ENTRY = (1501, "Failed deleting entry in database.")
    SQL_ERROR_CREATING_ENTRY_FOR_NEW_PERSON = (1502, "Failed creating entry in database for a new person.")
    SQL_PARAMETER_ERROR_DELETING_ENTRY = (1503, "Both first name and last name must be provided if personal ID is missing.")
    SQL_PARAMETER_ERROR_CREATING_NEW_PERSON = (1504, "Both first name and last name must be provided to create a person.")
    SQL_ERROR_READING_ENTRY_FOR_ALL_APARTMENTS = (1505, "Failed retrieving all apartments from the database.")
    SQL_ERROR_READING_ENTRY_FOR_ALL_PERSONS = (1506, "Failed retrieving all persons from the database.")
    SQL_ERROR_READING_ENTRY_FOR_ALL_TENANCIES = (1507, "Failed retrieving all tenancies from the database.")
    SQL_ERROR_READING_ENTRY_FOR_ALL_CONTRACTS = (1508, "Failed retrieving all contracts from the database.")
    SQL_PARAMETER_ERROR_UPDATING_ENTRY = (1509, "Both first name and last name must be provided if personal ID is missing.")
    SQL_ERROR_READING_SINGLE_PERSON = (1510, "Failed retrieving single person.")
    SQL_NO_FIELDS_PROVIDED_FOR_GET_SINGLE_PERSON = (1511, "No fields provided to retrieve a single person.")
    SQL_SUCH_PERSON_DOES_NOT_EXIST = (1512, "Such person does not exist in the database.")

    NOT_ALLOWED_NAME_FOR_NEW_ENTITY = (1600, "Not allowed name for creating a new entity in database.")
    ERROR_DOING_GET_QUERY_TO_AN_ENDPOINT = (1605, "Error doing GET query to an endpoint.")
    ERROR_DOING_POST_QUERY_TO_AN_ENDPOINT = (1606, "Error doing POST query to an endpoint")
    NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_CREATE_OPERATION = (1608, "System prompt for CREATE operation was not activated.")
    NO_ACTIVATION_OF_RESPONSE_FOR_CREATE_OPERATION = (1609, "Response for CREATE operation was not activated.")
    NO_ACTIVATION_OF_RESPONSE_FOR_DELETE_OPERATION = (1610, "Response for DELETE operation was not activated.")
    NO_ACTIVATION_OF_SYSTEM_PROMPT_FOR_DELETE_OPERATION = (1611, "System prompt for DELETE operation was not activated.")
    ERROR_PLACE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA = (1612, "Error placing entity to database or collecting missing data.")
    ERROR_DELETE_ENTITY_TO_DB_OR_COLLECT_MISSING_DATA = (1613, "Error deleting entity from database or collecting missing data.")
    ERROR_PLACE_ENTITY_TO_DB = (1614, "Error placing entity to database")
    ERROR_REMOVE_ENTITY_FROM_DB = (1615, "Error removing entity from database")

    # Flask error
    FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON = (2007, "HTTP request must have the JSON type")
    FLASK_ERROR_USER_QUESTION_IS_NOT_STRING = (2008, "User question is not a string")

    # Generic glue / parsing
    ERROR_PARSING_BOOLEAN_RESPONSE = (3001, "Failed parsing boolean response.")
    ERROR_INJECTING_FIELDS_TO_CREATE_PROMPT = (3002, "Failed injecting fields to CREATE prompt.")
    ERROR_INJECTING_FIELDS_TO_DELETE_PROMPT = (3003, "Failed injecting fields to DELETE prompt")
    ERROR_CALLING_FUNCTION = (3006, "Error calling function.")
    ERROR_INTERPRETING_THE_FUNCTION_CALL = (3007, "Error interpreting the LLM response.")
    ERROR_DECODING_THE_STRUCT_ANSWER_TO_JSON = (3008, "Error decoding the LLM response.")
    ERROR_PERFORMING_CRUD_OPERATION = (3009, "Failed performing CRUD operations.")
    TYPE_ERROR_CREATING_NEW_ENTRY = (3010, "That data type can not be created, because it is not covered in the databank system.")

    LOG_ERROR_FOR_FUNCTION_CALLING = (3012, "Error writing log for function calling.")

    WARNING_NOT_IMPLEMENTED = (9000, "Not implemented.")

    def __str__(self):
        error_code, error_text = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}"

    def __repr__(self):
        error_code, error_text = self
        return f"ErrorCode: error code: {error_code}. message: {error_text}"