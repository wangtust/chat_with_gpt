import os
import requests

API_URL = "https://api.chatanywhere.tech/v1/chat/completions"
API_KEY = "sk-uq2izeIe4JHRZzLZpuOevejJuBL2e297rHN629aP2z3SmT0M"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
MAX_TOKENS = 3000

def send_to_gpt(messages):
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "max_tokens": MAX_TOKENS
    }

    response = requests.post(API_URL, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}\nResponse: {response.text}")
        return None

    response_json = response.json()
    if 'choices' not in response_json:
        print(f"Error: 'choices' not found in response JSON\nResponse JSON: {response_json}")
        return None

    gpt_message = response_json['choices'][0]['message']['content']
    return gpt_message

def main():
    print("Welcome to the GPT-3.5 chat interface. Type 'q', 'Q', or 'quit' to exit.")
    messages = [{"role": "system", "content": "你是一个经验丰富的助手。"}]

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['q', 'quit']:
            print("Exiting...")
            break

        messages.append({"role": "user", "content": user_input})
        gpt_response = send_to_gpt(messages)
        if gpt_response:
            print("GPT: " + gpt_response)
            messages.append({"role": "assistant", "content": gpt_response})

if __name__ == "__main__":
    main()