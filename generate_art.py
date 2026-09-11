import os
import random
import requests
from datetime import datetime
from urllib.parse import quote

# 1. EXPANDED VARIABLE POOLS
characters = [
    "young male Chinese cultivator with a topknot bun", "mystical female spellcaster with glowing eyes", 
    "elderly martial arts master with a silver beard", "futuristic cyber-ninja in sleek traditional robes",
    "rogue technomancer with glowing neon tattoos", "divine Empress wielding a floating data-scroll"
]
outfits = [
    "flowing light-blue traditional Hanfu robes", "crimson silk robes embroidered with golden dragons", 
    "dark jade armor and tattered stealth cloaks", "pure white spiritual gowns woven from fiber-optics"
]
actions = [
    "interacting with a holographic matrix screen", "summoning a massive ring of floating digital runes", 
    "meditating deeply in front of a giant glowing server console", "drawing a katana made of condensed hard-light circuitry"
]
sci_fi = [
    "cascading green digital binary code streams", "vibrant neon cyan floating display holograms", 
    "pulsing purple circuit board lines etched in the air", "golden holographic ancient text and scriptures"
]
landscapes = [
    "a misty mountain range dotted with ancient traditional pagodas", "a hidden deep cave filled with glowing crystals and supercomputers", 
    "a bamboo forest overlapping with a towering cyberpunk cityscape", "a high-altitude temple floating silently amidst thunderclouds"
]

char = random.choice(characters)
outfit = random.choice(outfits)
action = random.choice(actions)
tech = random.choice(sci_fi)
land = random.choice(landscapes)

# 2. Assemble Master Prompt
prompt = f"Stunning modern Chinese manhua web novel cover style illustration, digital fantasy art, highly detailed. A {char}, wearing {outfit}, {action} featuring {tech}. Background is {land}, dramatic cinematic studio lighting, crisp focus, vibrant colors, masterpiece, 8k resolution."
print(f"Today's Generated Prompt: {prompt}")

# 3. Web-Safe Encoding (Safely wraps text variables so spaces and punctuation don't break the web request)
safe_prompt = quote(prompt)
seed_num = random.randint(1, 999999)

# 4. OFFICIAL GEN.POLLINATIONS.AI ROUTE STRUCTURE
url = f"https://gen.pollinations.ai/image/{safe_prompt}"

# 5. Connect query parameters mapping directly into standard GET fields
payload_parameters = {
    "width": 1024,
    "height": 1024,
    "model": "flux",
    "enhance": "true",
    "seed": seed_num
}

print("Connecting to official Pollinations API gateway infrastructure...")
response = requests.get(url, params=payload_parameters)

# 6. Build directory and write raw image payload
os.makedirs("generated_images", exist_ok=True)
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"generated_images/art_{timestamp_str}.jpg"

# 7. Verification fallback confirming data delivery
if response.status_code == 200 and b"html" not in response.content[:100]:
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved premium artwork asset to: {file_path}")
else:
    print(f"Error: API returned empty or broken data frame. Status: {response.status_code}")
