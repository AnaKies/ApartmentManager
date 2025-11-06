import inspect

from flask import Flask, jsonify, request
from flask_cors import CORS
from ApartmentManager.backend.SQL_API.rental.CRUD import create
from ApartmentManager.backend.config.server_config import HOST, PORT
import ApartmentManager.backend.SQL_API.rental.CRUD.read as read_sql
from ApartmentManager.backend.AI_API.general.conversation import LlmClient
from ApartmentManager.backend.AI_API.general.error_texts import APIError, ErrorCode
from ApartmentManager.backend.AI_API.general.api_data_type import build_error
from ApartmentManager.backend.AI_API.general.logger import init_logging, get_logger, log_error

# Initialize logger
init_logging()
logger = get_logger()

logger.info("Flask starting…")

app = Flask(__name__)

# allow route to the endpoint /api/
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Controls what the SQL table can return if a query has no parameters/filters.
DEFAULT_FIELDS_APARTMENT_TABLE = ["area", "address", "price_per_square_meter", "utility_billing_provider_id"]
ALLOWED_FIELDS = []

ai_client = LlmClient("Gemini")

@app.route('/')
def home():
    return 'OK'


@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    JSON-only endpoint for chat.
    Request JSON: { "user_input": "<string>" }
    Response JSON: { "question": "<string>", "answer": "<string>" }
    """
    if not request.is_json:
        trace_id = log_error(ErrorCode.FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON)
        raise APIError(ErrorCode.FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON, trace_id)

    # silent= True -> try to get JSON from an HTTP request
    data = request.get_json(silent=True)
    if data is None:
        data = {}

    value = data.get('user_input')
    user_question_str = value.strip() if value else ''
    print(user_question_str)

    if not user_question_str:
        trace_id = log_error(ErrorCode.FLASK_ERROR_USER_QUESTION_IS_NOT_STRING)
        raise APIError(ErrorCode.FLASK_ERROR_USER_QUESTION_IS_NOT_STRING, trace_id)

    model_answer = ai_client.get_llm_answer(user_question_str)
    print(model_answer)
    return model_answer, 200


@app.route('/tenancies', methods=['GET'])
def get_tenancies():
    """
     Returns a JSON list of tenancies.
    :return:
    """
    tenancies = read_sql.get_tenancies()
    tenancies_to_json = [tenancy.to_dict() for tenancy in tenancies]
    return jsonify(tenancies_to_json)


@app.route('/rent_data', methods=['GET'])
def get_contract():
    """
     Returns a JSON list of rent_data.
    :return:
    """
    rent_data = read_sql.get_contract()
    rent_data_to_json = [data.to_dict() for data in rent_data]
    return jsonify(rent_data_to_json)


@app.route('/persons', methods=['GET'])
def get_persons():
    """
     Returns a JSON list of persons.
    :return:
    """
    persons = read_sql.get_persons()
    persons_to_json = [person.to_dict() for person in persons]
    return jsonify(persons_to_json)



@app.route('/persons', methods=['POST'])
def add_person():
    """
    Adds new entry with personal data to the table with persons.
    The data to add are sent in the request body.
    Returns a status.
    :return:
    """
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415

    # silent= True -> try to get JSON from HTTP request
    # get payload from the body
    data_dict = request.get_json(silent=True)

    # get arguments from the signature of a function
    signature = inspect.signature(create.create_person)
    valid_params = signature.parameters.keys()
    filtered_params = {key: value for key, value in data_dict.items() if key in valid_params}

    result = create.create_person(**filtered_params) # unpack dictionary into function parameters
    return result, 200

@app.route('/apartments', methods=['GET'])
def get_apartments():
    """
    Returns a JSON list of apartments.
    :return:
    """
    apartments = read_sql.get_apartments()
    apartments_to_json = [apartment.to_dict() for apartment in apartments]
    return jsonify(apartments_to_json)


    """
    # SEARCHING FILTERS with values (restrict which rows are included in the result set. SQL: WHERE area = '60')
    area = request.args.get('area', type=float)
    address = request.args.get('address', type=str)
    price_per_square_meter = request.args.get('price_per_square_meter', type=float)
    utility_billing_provider_id = request.args.get('utility_billing_provider_id', type=int)


    # FIELDS PROJECTION (controls which columns to include in the result. SQL: SELECT)
    # Projection means returning only the specific fields explicitly requested instead of the entire record
    # Example: http://127.0.0.1:5003/apartments?area=16&fields=area,address
    query_fields = request.args.get('fields')
    # API allows the spaces around the filters in the API query.
    # Commas should separate filters.

    # If a query has no fields, default fields are used
    # Example: http://127.0.0.1:5003/apartments
    if query_fields:
        requested_fields = [filter_item.strip() for filter_item in query_fields.split(',')]
    else:
        requested_fields = DEFAULT_FIELDS_APARTMENT_TABLE

    unknown_fields = [field for field in requested_fields if field not in DEFAULT_FIELDS_APARTMENT_TABLE]
    if unknown_fields:
        abort(400, description=f"Unknown fields: {unknown_fields}")

    return jsonify({"fields": requested_fields}), 200
    """


# processes all exceptions in the business logic
@app.errorhandler(APIError)
def handle_api_error(api_error: APIError):
    print(api_error)
    result = build_error(code=api_error.code,
                         message=api_error.error_message,
                         llm_model=ai_client.model)

    return result, 500


# universal handler for all exceptions that were not catch ->
# prevent that the handler generates its own exception HTML page
@app.errorhandler(Exception)
def handle_unexpected_error(general_error):
    print(general_error)
    # Full server log
    app.logger.exception(general_error)

    # extract a message from a general error
    message = getattr(general_error, "error_message", None) or str(general_error) or "Unexpected error"

    result = build_error(code=-1,
                         message=message,
                         llm_model=ai_client.model)

    return result, 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=False)