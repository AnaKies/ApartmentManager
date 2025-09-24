from flask import Flask, jsonify, request, render_template_string
from ApartmentManager.backend.config.server_config import HOST, PORT
import ApartmentManager.backend.SQL_API.rentral.CRUD.read as read_sql
from ApartmentManager.backend.AI_API.general.conversation import AiConversationSession

app = Flask(__name__)

# Controls what the SQL table can return if a query has no parameters/filters.
DEFAULT_FIELDS_APARTMENT_TABLE = ["area", "address", "price_per_square_meter", "utility_billing_provider_id"]
ALLOWED_FIELDS = []

HOME_HTML = """
    <html><body>
        <h2>Welcome to the apartment manager</h2>
        <form action="/chat_mode" method="post">
            Your question: <input type='text' name='user_input'><br>
            <input type='submit' value='Continue'>
        </form>
        {% if question %}
            <div>
                <h3>Your Question:</h3>
                <p>{{ question }}</p>
            </div>
            <div>
                <h3>AI Answer:</h3>
                <p>{{ answer }}</p>
            </div>
        {% endif %}
    </body></html>"""


@app.route('/')
def home():
    return render_template_string(HOME_HTML)


@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    JSON-only endpoint for chat.
    Request JSON: { "user_input": "<string>" }
    Response JSON: { "question": "<string>", "answer": "<string>" }
    """
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415

    data = request.get_json(silent=True) or {}
    user_input = (data.get('user_input') or '').strip()

    if not user_input:
        return jsonify(error="`user_input` is required"), 400

    ai_client = AiConversationSession("Gemini")
    try:
        model_answer = ai_client.get_ai_answer(user_input)
        return jsonify(question=user_input, answer=model_answer), 200
    except Exception:
        app.logger.exception("chat_api error")
        return jsonify(error="internal_error"), 500

@app.route('/chat_mode', methods=['GET', 'POST'])
def chat_mode():
    """
    Endpoint for conversation between AI and user in chat mode.
    :param user_input: Input from user.
    :return: Data with user questions and AI answer in human like format.
    """
    ai_client = AiConversationSession("Gemini")

    if request.method == 'POST':
        # Holen Sie die Benutzereingabe aus dem POST-Formular
        user_input = request.form.get('user_input')
        if user_input:
            model_answer = ai_client.get_ai_answer(user_input)
            # Rendern Sie die gleiche Seite mit Frage und Antwort
            return render_template_string(HOME_HTML, question=user_input, answer=model_answer)
        else:
            # Falls die Eingabe leer ist
            return render_template_string(HOME_HTML, answer="Please provide a question.")

    # Für GET-Anfragen (direkter Aufruf oder erster Seitenaufruf)
    return render_template_string(HOME_HTML)


@app.route('/apartments', methods=['GET'])
def get_apartments():
    """
    Returns a JSON list of apartments with
    :return:
    """
    try:
        apartments = read_sql.get_apartments()
        apartments_to_json = [apartment.to_dict() for apartment in apartments]
        return jsonify(apartments_to_json)
    except Exception as error:
        return jsonify({"error": "Internal server error", "message": str(error)}), 500

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

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error.description)}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)