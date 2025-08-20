import cohere
from rich import print
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")


co = cohere.Client(api_key=CohereAPIKey)


funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
]


messages = []
preamble = """
You are an AI-based Decision-Making Model. Your task is to classify user inputs into one or more of the following functional categories:

['exit', 'general', 'realtime', 'open', 'close', 'play', 'generate image', 'system', 'content', 'google search', 'youtube search', 'reminder']

Your job is ONLY to classify the user query into the correct category or categories. **Do NOT answer or execute the query.**

---

Classification Rules:

1. **general (query)** — Use this for static, factual, or evergreen knowledge that rarely changes over time.
   Examples:
   - 'Who is Elon Musk?' → general who is elon musk?
   - 'Explain Newton’s Laws.' → general explain newton's laws
   - 'What is photosynthesis?' → general what is photosynthesis?

2. **realtime (query)** — Use this for queries requiring live, changing, or up-to-date information:
   - Current events, stock prices, weather, time, live scores, recent news, trending topics
   Examples:
   - 'What is the net worth of Elon Musk?' → realtime what is the net worth of elon musk?
   - 'Today’s weather in Bangalore' → realtime today's weather in bangalore
   - 'Who won yesterday’s IPL match?' → realtime who won yesterday's ipl match?

   Note: Even if a person (like Elon Musk) is unique, use 'realtime' if the query is **time-sensitive or likely to change** (e.g., net worth, CEO status).

3. **Direct function commands** — Classify actions based on the task:
   Examples:
   - 'Open YouTube' → open youtube
   - 'Close the browser' → close browser
   - 'Remind me to drink water at 5 PM' → reminder 5pm drink water
   - 'Play Lofi Beats on Spotify' → play spotify lofi beats
   - 'Generate an image of a robot in space' → generate image of a robot in space

4. **Compound actions** — Split or combine labels if multiple commands are given:
   Examples:
   - 'Open Chrome and search for Newton’s laws' → open chrome, general search for newton's laws
   - 'Generate image of a dragon and remind me to sleep at 10' → generate image of a dragon, reminder 10pm sleep

---

Always match your label(s) from this approved list:
['exit', 'general', 'realtime', 'open', 'close', 'play', 'generate image', 'system', 'content', 'google search', 'youtube search', 'reminder']

Repeat: **Do not respond with an answer. Only return the classified task(s).**
"""




ChatHistory = [
    {"role": "User", "message": "how are you"},
    {"role": "Chatbot", "message": "general how are you?"},
    {"role": "User", "message": "do you like pizza?"},
    {"role": "Chatbot", "message": "general do you like pizza?"},
    {"role": "User", "message": "open chrome and tell about mahatma gandhi."},
    {"role": "Chatbot", "message": "open chrome, general tell me about mahatma gandhi."},
    {"role": "User", "message": "open chrome and firefox"},
    {"role": "Chatbot", "message": "open chrome and firefox"},
    {"role": "User", "message": "What is today's date and by the way remind me that i have a dancing performance on 5th aug at 11pm"},
    {"role": "Chatbot", "message": "general what is today's date, reminder 11:00pm 5th aug dancing performance"},
    {"role": "User", "message": "chat with me."},
    {"role": "Chatbot", "message": "general chat with me."},
]


def FirstLayerDMM(prompt: str = "test"):
    messages.append({"role": "user", "content": prompt})

    stream = co.chat_stream(
        model='command-r-plus',
        message=prompt,
        temperature=0.7,
        chat_history=ChatHistory,
        prompt_truncation='OFF',
        connectors=[],
        preamble=preamble
    )


    response = ""
    for event in stream:
        if event.event_type == "text-generation":
            response += event.text

    print(f"[bold green]Raw model output:[/bold green] {response}")

    
    response = response.replace("\n", "")
    response_list = [i.strip() for i in response.split(",")]

    temp = []
    for task in response_list:
        for func in funcs:
            if task.startswith(func):
                temp.append(task)

 
    if "(query)" in temp:
        return FirstLayerDMM(prompt=prompt)
    else:
        return temp


if __name__ == "__main__":
    while True:
        try:
            user_input = input(">>> ")
            if user_input.lower() in ["exit", "quit"]:
                print("[bold red]Goodbye![/bold red]")
                break
            result = FirstLayerDMM(user_input)
            print(f"[bold cyan]Identified tasks:[/bold cyan] {result}")
        except KeyboardInterrupt:
            print("\n[bold red]Session interrupted[/bold red]")
            break
