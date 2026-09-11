import os
import random
import requests
from datetime import datetime

# 1. EXPANDED HYPER-DETAILED ART POOLS
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

# 2. Premium descriptive prompt structure
prompt = f"Stunning modern Chinese manhua web novel cover style illustration, digital fantasy art, highly detailed. A {char}, wearing {outfit}, {action} featuring {tech}. Background is {land}, dramatic cinematic studio lighting, crisp focus, vibrant colors, masterpiece, 8k resolution."
print(f"Today's Prompt: {prompt}")

# 3. BASE API LINK (Kept ultra-short to ensure URL structure never overflows)
url = "https://pollinations.ai"

# 4. Standard GET parameters mapping (Moves prompt out of path, into safe query args)
payload_parameters = {
    "prompt": prompt,
    "width": 1024,
    "height": 1024,
    "model": "flux",
    "enhance": "true",
    "nologo": "true",
    "seed": random.randint(1, 999999)
}

# 5. Extract token from vault and structure it as a secure authentication cookie
token = os.environ.get("POLLINATIONS_TOKEN")
headers = {}
if token:
    headers["Cookie"] = f"__Secure-better-auth.session_token={token}"

print("Sending optimized safe GET request to Pollinations API...")
# Using standard requests.get with dictionary arguments passes long text reliably
response = requests.get(url, params=payload_parameters, headers=headers)

# 6. Verify and save the high-quality output
os.makedirs("generated_images", exist_ok=True)
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"generated_images/art_{timestamp_str}.jpg"

if response.status_code == 200 and b"html" not in response.content[:100]:
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved authenticated artwork to: {file_path}")
else:
    print(f"Error: API failed to return an image. Code: {response.status_code}")
