import inspect
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Blueprint, current_app
from flask_cors import CORS
from requests import RequestException
from werkzeug.exceptions import HTTPException
from google.genai import errors as genai_errors
from ApartmentManager.backend.SQL_API.rental.CRUD import create
from ApartmentManager.backend.config.server_config import HOST, PORT
import ApartmentManager.backend.SQL_API.rental.CRUD.read as read_sql
from ApartmentManager.backend.AI_API.general.conversation_client import ConversationClient
from ApartmentManager.backend.AI_API.general.error_texts import APIError, ErrorCode
from ApartmentManager.backend.AI_API.general.envelopes.envelopes_api import build_error, AnswerSource
from ApartmentManager.backend.AI_API.general.logger import init_logging, get_logger, log_error

# Helps access the decorator names after initialization
public_bp = Blueprint("public_api", __name__) # http://HOST:PORT/api/...
internal_bp = Blueprint("internal_api", __name__) #http://HOST:PORT/...

def initialize():
    # Initialize logger
    init_logging()
    logger = get_logger()

    logger.info("Flask starting…")

    flask_app = Flask(__name__)

    # allow route to the endpoint /api/ and /internal/ to be accessed from any origin
    CORS(flask_app, resources={r"/api/*": {"origins": "*"},
                               r"/internal/*": {"origins": "*"}})

    # Specify the model to use
    load_dotenv()
    some_gemini_model = os.getenv("GEMINI_MODEL")  # for example, gemini-2.5-flash

    # Here we put the object of LlmClient inside the extension of the Flask app
    # Then we can access it from any route inside the app using current_app.extensions["ai_client"]
    flask_app.extensions = getattr(flask_app, "extensions", {})
    flask_app.extensions["ai_client"] = ConversationClient(some_gemini_model)

    # register routes/error handlers defined on the both blueprints
    flask_app.register_blueprint(public_bp)
    flask_app.register_blueprint(internal_bp, url_prefix='/internal')

    return flask_app

@public_bp.route('/')
def home():
    return 'OK'


@public_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """
    JSON-only endpoint for chat.
    Request JSON: { "user_input": "<string>" }
    """
    try:
        if not request.is_json:
            trace_id = log_error(ErrorCode.FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON)
            raise APIError(ErrorCode.FLASK_ERROR_HTTP_REQUEST_INPUT_MUST_BY_JSON, trace_id)

        # silent= True -> try to get JSON from an HTTP request
        data = request.get_json(silent=True)
        if data is None:
            data = {}

        # The API defines and expects this key in the request body
        value = data.get('user_input')
        user_question_str = value.strip() if value else ''
        print(user_question_str)

        if not user_question_str:
            trace_id = log_error(ErrorCode.FLASK_ERROR_USER_QUESTION_IS_NOT_STRING)
            raise APIError(ErrorCode.FLASK_ERROR_USER_QUESTION_IS_NOT_STRING, trace_id)

        # current_app is the variable of Flask that points to the actual app
        # Different objects of the business logic can be stored inside
        ai_client = current_app.extensions["ai_client"]

        # LLM answers
        model_answer = ai_client.get_llm_answer(user_question_str)

        result = model_answer.model_dump(mode='json')

        print(result)
        return result, 200
        # TODO implement close client to release the http resources

    except APIError:
        raise
    except genai_errors.APIError:
        raise
    except RequestException:
        raise
    except Exception:
        raise

@internal_bp.route('/tenancies', methods=['GET'])
def get_tenancies():
    """
     Returns a JSON list of tenancies.
    :return:
    """
    tenancies = read_sql.get_tenancies()
    tenancies_to_json = [tenancy.to_dict() for tenancy in tenancies]
    return jsonify(tenancies_to_json)


@internal_bp.route('/contract', methods=['GET'])
def get_contract():
    """
     Returns a JSON list of contracts.
    :return:
    """
    contracts = read_sql.get_contract()
    contracts_to_json = [data.to_dict() for data in contracts]
    return jsonify(contracts_to_json)


@internal_bp.route('/persons', methods=['GET'])
def get_persons():
    """
     Returns a JSON list of persons.
    :return:
    """
    persons = read_sql.get_persons()
    persons_to_json = [person.to_dict() for person in persons]
    return jsonify(persons_to_json)


@internal_bp.route('/persons', methods=['POST'])
def add_person():
    """
    Adds new entry with personal data to the table with persons.
    The data to add is sent in the request body.
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

@internal_bp.route('/apartments', methods=['GET'])
def get_apartments():
    """
    Returns a JSON list of apartments.
    :return:
    """
    apartments = read_sql.get_apartments()
    apartments_to_json = [apartment.to_dict() for apartment in apartments]
    return jsonify(apartments_to_json)


# processes all exceptions in the business logic
@public_bp.app_errorhandler(APIError)
def handle_api_error(api_error: APIError):
    result = build_error(code=api_error.error_code,
                         message=api_error.message,
                         llm_model=current_app.extensions["ai_client"].model_name,
                         answer_source=AnswerSource.BACKEND,
                         trace_id=api_error.trace_id if hasattr(api_error, "trace_id") else "")
    return result.model_dump(mode='json'), 200


@public_bp.app_errorhandler(HTTPException)
def handle_http_error(http_err: HTTPException):
    message = getattr(http_err, "description", None) or str(http_err) or "HTTP error"
    result = build_error(
        code=http_err.code,
        message=message,
        llm_model=current_app.extensions["ai_client"].model_name,
        answer_source=AnswerSource.BACKEND,
        trace_id=getattr(http_err, "trace_id", "-")
    )
    return result.model_dump(mode='json'), http_err.code


# universal handler for all exceptions that were not catch ->
# prevent that the handler generates its own exception HTML page
@public_bp.app_errorhandler(Exception)
def handle_unexpected_error(general_error):
    # Full server log
    current_app.logger.exception(general_error)

    # extract a message from a general error
    message = getattr(general_error, "error_message", None) or str(general_error) or "Unexpected error"

    result = build_error(code=-1,
                         message=message,
                         llm_model=current_app.extensions["ai_client"].model_name,
                         answer_source=AnswerSource.BACKEND,
                         trace_id=general_error.trace_id if hasattr(general_error, "trace_id") else "-")

    return result.model_dump(mode='json'), 500

@public_bp.app_errorhandler(genai_errors.APIError)
def handle_gemini_api_error(err: genai_errors.APIError):
    trace_id = log_error(exception=err)

    # Extract HTTP-code and message from the exception
    status_code = getattr(err, "code", None)
    if not status_code:
        # try to get the response_json
        status_code = (getattr(err, "response_json", {}) or {}).get("error", {}).get("code", 500)
    message = getattr(err, "message")
    if not message:
        message = str(err)

    result = build_error(
        code=status_code,
        message=message,
        llm_model=current_app.extensions["ai_client"].model_name,
        answer_source=AnswerSource.BACKEND,
        trace_id=trace_id
    )
    return result.model_dump(mode='json'), int(status_code or 500)

if __name__ == '__main__':
    app = initialize()
    app.run(host=HOST, port=PORT, debug=False)