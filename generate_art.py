import os
import random
import requests
from datetime import datetime
from urllib.parse import quote

# 1. CLEAN VARIABLES (Slightly shorter to guarantee the URL never breaks)
characters = [
    "male Chinese cultivator with a topknot bun", 
    "female spellcaster with glowing eyes", 
    "martial arts master with a silver beard", 
    "cyber-ninja in sleek traditional robes"
]
outfits = [
    "flowing traditional Hanfu robes", 
    "silk robes embroidered with dragons", 
    "dark jade armor and tattered cloaks", 
    "white spiritual gowns"
]
actions = [
    "interacting with a holographic screen", 
    "summoning a ring of digital runes", 
    "meditating in front of a giant server console", 
    "drawing a katana made of circuitry"
]
sci_fi = [
    "green digital binary code", 
    "vibrant neon cyan holograms", 
    "pulsing purple circuit board lines", 
    "golden holographic ancient script"
]
landscapes = [
    "a misty mountain range with pagodas", 
    "a cave filled with glowing crystals and servers", 
    "a bamboo forest overlapping with a cyberpunk city", 
    "a temple floating amidst thunderclouds"
]

# 2. Pick one randomly
char = random.choice(characters)
outfit = random.choice(outfits)
action = random.choice(actions)
tech = random.choice(sci_fi)
land = random.choice(landscapes)

# 3. Clean Master Prompt (Puts style tags at the front)
prompt = f"Modern Chinese manhua cover style digital art, highly detailed. A {char}, wearing {outfit}, {action} featuring {tech}, background is {land}, cinematic lighting, 8k resolution."
print(f"Today's Prompt: {prompt}")

# 4. Convert text safely so commas and spaces don't break the web link
safe_prompt = quote(prompt)
seed = random.randint(1, 99999)

# 5. Native URL Structure forcing the high-quality FLUX model and removing logo
url = f"https://pollinations.ai{safe_prompt}?width=1024&height=1024&model=flux&enhance=true&nologo=true&seed={seed}"

# 6. THE MASK: This tricks the Pollinations server into thinking a human is clicking a link
# on Google Chrome, bypassing the automated low-quality cloud restriction lane.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Requesting image from Pollinations...")
response = requests.get(url, headers=headers)

# 7. Create the folder and save the image with an exact timestamp
os.makedirs("generated_images", exist_ok=True)
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"generated_images/art_{timestamp_str}.jpg"

# 8. Check that we got a real image, not an error page
if response.status_code == 200 and b"html" not in response.content[:100]:
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved pristine image file to: {file_path}")
else:
    print(f"Error: API returned empty or broken data frame. Status: {response.status_code}")
