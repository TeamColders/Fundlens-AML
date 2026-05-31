from google import genai

API_KEY = ""

client = genai.Client(api_key=API_KEY)

chat = client.chats.create(model="gemini-3.5-flash")

print("Gemini Chatbot (type 'exit' to quit)\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    response = chat.send_message(user_input)

    print(f"Bot: {response.text}\n")