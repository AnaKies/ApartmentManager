from ApartmentManager.backend.AI_API.ai_clients.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.ai_clients.groq_client import GroqClient

def main():
    while True:
        ai_client = None
        model_choice = int(input("""Which AI model do you want to use?
         1. Gemini
         2. Groq \n"""))

        if model_choice == 1:
            ai_client = GeminiClient()
            print("Gemini will answer your question.")
        elif model_choice == 2:
            ai_client = GroqClient()
            print("Groq will answer your question.")

        # User asks a question
        user_question = input("Ask me something about apartments: ")

        # Answer of AI with function call inside
        answer = ai_client.get_ai_function_call(user_question)
        print(answer)
"""
        # AI generates a query
        query_json = ai_client.ai_generate_json_data_for_sql_query(user_question)
        print("......AI generated query:", query_json)

        # Python script executes the query
        api_response = ai_client.call_endpoint_restful_api(query_json)
        print("......RESTFUL API returned data:", api_response)

        # AI generates a human friendly answer
        ai_answer = ai_client.represent_ai_answer(api_response, user_question)
        print(ai_answer)
"""

if __name__ == "__main__":
    main()