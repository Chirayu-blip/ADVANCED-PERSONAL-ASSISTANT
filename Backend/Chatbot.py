from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os


env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)


System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot = [
    {"role": "system", "content": System}
]


os.makedirs("Data", exist_ok=True)


try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    messages = []


def RealtimeInformation():
    current_data_time = datetime.datetime.now()
    return current_data_time.strftime("Today is %A, %d %B %Y, %H:%M:%S")


def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def ChatBot(Query):
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        messages.append({"role": "user", "content": Query})

        full_messages = SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=full_messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error: {e}")
        
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)


if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))
