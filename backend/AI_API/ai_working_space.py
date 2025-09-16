import json

from ApartmentManager.backend.AI_API.ai_clients.gemini.gemini_client import GeminiClient
from ApartmentManager.backend.AI_API.ai_clients.groq.groq_client import GroqClient

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

def main():
    while True:
        # User asks a question
        user_question = input("Ask me something about apartments: ")

        # structured output for the later implementation of GUI
        if user_question == "Show apartments":
            answer_with_apartments = ai_client.process_function_call_request(user_question)
            answer_show = ai_client.get_structured_ai_response(answer_with_apartments)
            print(json.dumps(answer_show, indent=4))
            continue

        # Answer of AI with function call inside
        answer = ai_client.process_function_call_request(user_question)
        print(answer)


if __name__ == "__main__":
    main()