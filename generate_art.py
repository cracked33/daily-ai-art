import os
import random
import requests
from datetime import datetime

# 1. Lists of variables to mix and match automatically every day
characters = ["young male Chinese cultivator with a topknot bun", "mystical female spellcaster with glowing eyes", "elderly martial arts master with a silver beard", "futuristic cyber-ninja in sleek traditional robes"]
outfits = ["flowing light-blue traditional Hanfu robes", "crimson silk robes embroidered with golden dragons", "dark jade armor and tattered cloaks", "pure white spiritual gowns"]
actions = ["interacting with a holographic matrix", "summoning a ring of floating digital runes", "meditating in front of a glowing server console", "drawing a sword made of hard-light circuitry"]
sci_fi = ["green digital binary code", "vibrant neon cyan holograms", "pulsing purple circuit board lines", "golden holographic ancient script"]
landscapes = ["a misty mountain range with traditional pagodas", "a hidden cave filled with glowing crystals and servers", "a bamboo forest overlapping with a cyberpunk cityscape", "a high-altitude temple floating amidst thunderclouds"]

# 2. Pick one randomly from each list
char = random.choice(characters)
outfit = random.choice(outfits)
action = random.choice(actions)
tech = random.choice(sci_fi)
land = random.choice(landscapes)

# 3. Assemble the Master Prompt
prompt = f"A {char}, wearing {outfit}, {action} featuring {tech}. Background is {land}, cinematic lighting, modern Chinese manhua web novel cover style, digital fantasy art, highly detailed, 8k resolution."
print(f"Today's Prompt: {prompt}")

# 4. Request the image from Pollinations.ai (Free, no login needed)
url = f"https://pollinations.ai{requests.utils.quote(prompt)}?width=1024&height=1024&enhance=true&seed={random.randint(1, 99999)}"
response = requests.get(url)

# 5. Create a folder and save the image with today's date
os.makedirs("generated_images", exist_ok=True)
date_str = datetime.now().strftime("%Y-%m-%d")
file_path = f"generated_images/art_{date_str}.jpg"

if response.status_code == 200:
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved: {file_path}")
else:
    print("Failed to download image.")
