import asyncio
from random import randint
from PIL import Image
import requests 
from dotenv import get_key
import os 
from time import sleep

# Function to display images after generation
def open_image(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")
    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"🖼️ Opening image: {image_path}")
            img.show()
            sleep(1)
        except FileNotFoundError:
            print(f"❌ Unable to open image: {image_path}")

# Hugging Face Stable Diffusion API
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}

# Async POST request to HuggingFace
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response

# Generate 4 images concurrently
async def generate_images(prompt: str):
    tasks = []
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, Ultra High details, high resolution, seed={randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    print("⏳ Generating images... Please wait...")

    image_responses = await asyncio.gather(*tasks)

    os.makedirs("Data", exist_ok=True)
    for i, image_response in enumerate(image_responses):
        if image_response.status_code == 200:
            filename = f"Data/{prompt.replace(' ', '_')}{i + 1}.jpg"
            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"✅ Saved: {filename}")
        else:
            print(f"❌ Error from HuggingFace API: {image_response.status_code} - {image_response.text}")

# Main entry point to generate and show
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_image(prompt)

# Main loop to listen for task trigger
# Main loop to listen for task trigger
while True:
    try:
        with open(r"Frontend\Files\ImageGeneration.data", "r") as f:
            lines = f.readlines()

        found = False

        for idx, line in enumerate(lines):
            line = line.strip()

            if not line or "," not in line:
                continue

            parts = line.split(",")
            if len(parts) == 2:
                Prompt, Status = parts
                Prompt = Prompt.strip()
                Status = Status.strip().lower()

                if Status == "true":
                    print(f"📌 Found prompt: '{Prompt}'")

                    # Mark that line as processed by setting it to "False,False"
                    lines[idx] = "False,False\n"
                    with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                        f.writelines(lines)

                    GenerateImages(Prompt)
                    found = True
                    break

        if not found:
            print("📭 No active prompt found. Waiting...")
            sleep(1)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        sleep(1)

