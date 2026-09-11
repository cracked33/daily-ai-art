import os
import random
import requests
from datetime import datetime
from urllib.parse import quote

# 1. HYPER-DETAILED ART VARIABLE POOLS
characters = [
    "young male Chinese cultivator with a topknot bun", "mystical female spellcaster with glowing eyes", 
    "elderly martial arts master with a silver beard", "futuristic cyber-ninja in sleek traditional robes"
]
outfits = [
    "flowing light-blue traditional Hanfu robes", "crimson silk robes embroidered with golden dragons", 
    "dark jade armor and tattered stealth cloaks"
]
actions = [
    "interacting with a holographic matrix screen", "summoning a massive ring of floating digital runes", 
    "meditating deeply in front of a giant glowing server console"
]
sci_fi = [
    "cascading green digital binary code streams", "vibrant neon cyan floating display holograms", 
    "pulsing purple circuit board lines etched in the air"
]
landscapes = [
    "a misty mountain range dotted with ancient traditional pagodas", "a hidden deep cave filled with glowing crystals and supercomputers", 
    "a bamboo forest overlapping with a towering cyberpunk cityscape"
]

char = random.choice(characters)
outfit = random.choice(outfits)
action = random.choice(actions)
tech = random.choice(sci_fi)
land = random.choice(landscapes)

# 2. Assemble Master Prompt
prompt = f"Stunning modern Chinese manhua web novel cover style illustration, digital fantasy art, highly detailed. A {char}, wearing {outfit}, {action} featuring {tech}. Background is {land}, dramatic cinematic studio lighting, crisp focus, vibrant colors, masterpiece, 8k resolution."
print(f"Today's Prompt: {prompt}")

# 3. Clean encoding to bypass special characters
safe_prompt = quote(prompt)
seed = random.randint(1, 999999)

# 4. Standard modern API endpoint (Using the verified gen.pollinations.ai hub)
url = f"https://gen.pollinations.ai/image/{safe_prompt}?width=1024&height=1024&model=flux&enhance=true&seed={seed}"

print("Calling Pollinations cluster node...")
response = requests.get(url)

if response.status_code == 200:
    try:
        # Check if the API returned a JSON link layout (Modern 2026 Pollinations architecture)
        response_json = response.json()
        image_download_url = response_json.get("url")
        print(f"Image processed! Retrieving raw image binary from cloud node: {image_download_url}")
        
        # Open and download the actual raw photo file from the cloud link
        image_response = requests.get(image_download_url)
        content_to_save = image_response.content
    except Exception:
        # Fallback layer: If the API immediately streams raw data, capture it directly
        content_to_save = response.content

    # 5. Build folder and save the absolute image binary file cleanly
    os.makedirs("generated_images", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"generated_images/art_{timestamp_str}.jpg"
    
    with open(file_path, "wb") as f:
        f.write(content_to_save)
    print(f"Successfully saved pristine image asset to: {file_path}")
else:
    print(f"Error: API network node rejected data payload. Code: {response.status_code}")
