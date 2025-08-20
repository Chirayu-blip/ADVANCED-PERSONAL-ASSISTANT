from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
import time

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# Create HTML for speech recognition
HtmlCode = """<!DOCTYPE html>
<html lang="en">
<head>
  <title>Speech Recognition</title>
</head>
<body>
  <button id="start" onclick="startRecognition()">Start Recognition</button>
  <button id="end" onclick="stopRecognition()">Stop Recognition</button>
  <p id="output"></p>

  <script>
    const output = document.getElementById('output');
    let recognition;

    function startRecognition() {
      recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      recognition.lang = '';
      recognition.continuous = true;

      recognition.onresult = function(event) {
        const transcript = event.results[event.results.length - 1][0].transcript;
        output.textContent += transcript + " ";
      };

      recognition.onend = function() {
        recognition.start();
      };

      recognition.start();
    }

    function stopRecognition() {
      recognition.stop();
    }
  </script>
</body>
</html>"""

# Set the recognition language in the HTML
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Save the HTML file
os.makedirs("Data", exist_ok=True)
with open("Data/Voice.html", "w", encoding='utf-8') as f:
    f.write(HtmlCode)

# Get full path to the HTML file
current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36")
# Do NOT use headless mode, as speech recognition requires visible tab

# Start Chrome driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Folder path for status file
TempDirPath = os.path.join(current_dir, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

# Function to write assistant status
def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "Status.data"), "w", encoding='utf-8') as file:
        file.write(Status)

# Function to clean/modify query
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word in new_query for word in question_words):
        new_query = new_query.rstrip(".?!") + "?"
    else:
        new_query = new_query.rstrip(".?!") + "."

    return new_query.capitalize()

# Translate to English if needed
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()


def SpeechRecognition(timeout=15):
    driver.get("file:///" + Link)
    driver.find_element(By.ID, "start").click()

    print("[INFO] Listening... Speak now.")
    start_time = time.time()

    while True:
        try:
            Text = driver.find_element(By.ID, "output").text.strip()

            if Text:
                driver.find_element(By.ID, "end").click()
                print(f"[INFO] Recognized text: {Text}")

                if "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))

            # Timeout condition
            if time.time() - start_time > timeout:
                driver.find_element(By.ID, "end").click()
                print("[WARN] Timeout reached. No input detected.")
                return None

        except Exception:
            pass

# Main loop
if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        if text:
            print(f"[RESULT] Final Query: {text}")
        else:
            break
