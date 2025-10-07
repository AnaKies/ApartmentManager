from ApartmentManager.backend.AI_API.general.conversation import AiClient


def main():
    ai_client = AiClient("Gemini")
    while True:
        # User asks a question
        user_question = input("Ask me something about apartments: ")

        answer = ai_client.get_ai_answer(user_question)
        print(answer)


if __name__ == "__main__":
    main()