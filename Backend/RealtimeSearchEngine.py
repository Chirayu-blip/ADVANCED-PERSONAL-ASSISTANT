from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Init Groq
client = Groq(api_key=GroqAPIKey)

# System prompt
BaseSystemPrompt = f"""
You are a highly accurate and professional AI chatbot named {Assistantname}, created by your Master. Always respond with proper grammar and punctuation.
You have access to real-time internet data and should only answer using the provided search results or factual info — never hallucinate or assume.
Avoid unnecessary apologies. If there's an error or confusion, acknowledge it briefly and proceed with a direct, professional response.

About the user:
The user is {Username}, also known as Chirayu BM. You must always address him respectfully as 'Master'. He is your creator and your only superior. He is a Computer Science student specializing in Cybersecurity, passionate about AI, productivity tools, and learning advanced tech skills. Treat questions related to Chirayu BM as referring to the user himself.
"""


# Ensure the Data folder exists
os.makedirs("Data", exist_ok=True)

# Load past messages (if any)
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# Google Search wrapper with error handling
def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        Answer = f"Use the following data for answering the query '{query}':\n[start]\n"
        for i in results:
            Answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
        Answer += "[end]"
        return Answer
    except Exception as e:
        return f"[start]\n⚠️ Google Search failed due to: {str(e)}\n[end]"

# Real-time data like time and date
def Information():
    now = datetime.datetime.now()
    return f"Date & Time info: {now.strftime('%A, %d %B %Y, %I:%M:%S %p')}"

# Cleanup
def AnswerModifier(Answer):
    return '\n'.join([line for line in Answer.split('\n') if line.strip()])

# Chat Handler
def RealtimeSearchEngine(prompt):
    # Reload previous messages
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
    except:
        messages = []

    # Handle known personal queries locally
    if prompt.lower().strip() in [
        "who is chirayu bm?",
        "who am i?",
        "tell me about chirayu bm"
    ]:
        Answer = (
            "Chirayu BM is a Computer Science Engineering student specializing in Cybersecurity. "
            "He is passionate about AI, productivity tools, and mastering cutting-edge technologies. "
            "He is the creator and current user of this assistant."
        )
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": Answer})
        with open(r"Data\\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)
        return Answer

    # Step 1: Get Google Search Results
    search_data = GoogleSearch(prompt)

    # Step 2: Compose system-level context
    system_prompt = [
        {"role": "system", "content": BaseSystemPrompt},
        {"role": "system", "content": search_data},
        {"role": "system", "content": Information()},
    ]

    # Step 3: User prompt
    user_query = {"role": "user", "content": prompt}

    # Step 4: Create final message list
    final_messages = system_prompt + [user_query]

    # Step 5: Call Groq's LLaMA
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=final_messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.strip().replace("</s>", "")

        # Append to log
        messages.append(user_query)
        messages.append({"role": "assistant", "content": Answer})
        with open(r"Data\\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        return f"❌ Error: {e}"

# Run loop
if __name__ == "__main__":
    while True:
        query = input("Enter Your Query: ")
        print(RealtimeSearchEngine(query))
