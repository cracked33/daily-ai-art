import os
import random
import requests
from datetime import datetime
from urllib.parse import quote

# 1. EXPANDED MASSIVE VARIABLE POOLS
characters = [
    "young male Chinese cultivator with a topknot bun", "mystical female spellcaster with glowing eyes", 
    "elderly martial arts master with a silver beard", "futuristic cyber-ninja in sleek traditional robes",
    "rogue technomancer with glowing neon tattoos", "divine Empress wielding a floating data-scroll",
    "steampunk alchemist mixing digital potions", "cybernetic shadow-assassin with holographic fox ears",
    "ancient celestial deity manifesting as a glowing android", "wandering ronin with a plasma-edged katana",
    "grand magus decoding binary star charts", "armored paladin with illuminated circuitry runes"
]

outfits = [
    "flowing light-blue traditional Hanfu robes", "crimson silk robes embroidered with golden dragons", 
    "dark jade armor and tattered stealth cloaks", "pure white spiritual gowns woven from fiber-optics",
    "midnight black leather coats lined with neon cyan strips", "traditional gold-leaf ceremonial armor",
    "shadowy carbon-fiber robes with glowing seams", "emerald green silk kimonos decorated with digital matrix patterns",
    "iridescent holographic cloaks that shift colors", "heavy battle-exoskeleton layered over ancient wraps"
]

actions = [
    "interacting with a holographic matrix screen", "summoning a massive ring of floating digital runes", 
    "meditating deeply in front of a giant glowing server console", "drawing a katana made of condensed hard-light circuitry",
    "weaving a web of emerald-green streaming energy", "hacking into an ancient spiritual mainframe",
    "manifesting ethereal data-wings from their back", "channeling lightning bolts through a microchip talisman",
    "floating mid-air while surrounded by spinning code scrolls", "shattering a digital security barrier with an open palm strike"
]

sci_fi = [
    "cascading green digital binary code streams", "vibrant neon cyan floating display holograms", 
    "pulsing purple circuit board lines etched in the air", "golden holographic ancient text and scriptures",
    "shimmering glitch effects and pixelated energy arcs", "swirling fields of blue nanite dust particles",
    "floating geometric data arrays and radar grids", "arcs of hyper-dense violet plasma electricity",
    "spinning holographic clockwork gears and matrix equations", "blazing crimson fire walls made of literal code segments"
]

landscapes = [
    "a misty mountain range dotted with ancient traditional pagodas", "a hidden deep cave filled with glowing crystals and supercomputers", 
    "a bamboo forest overlapping with a towering cyberpunk cityscape", "a high-altitude temple floating silently amidst thunderclouds",
    "an neon-drenched market street filled with traditional market stalls", "a monolithic server farm shaped like a traditional step-pyramid",
    "a serene cherry blossom garden beneath a digital neon sky grid", "a dramatic cliffside overlook facing a sea of data clouds",
    "the interior of an opulent throne room lit by giant holographic projection screens", "a futuristic dojo floating in deep outer space"
]

# 2. Pick one randomly from each list
char = random.choice(characters)
outfit = random.choice(outfits)
action = random.choice(actions)
tech = random.choice(sci_fi)
land = random.choice(landscapes)

# 3. Assemble the Master Prompt
raw_prompt = f"A {char}, wearing {outfit}, {action} featuring {tech}. Background is {land}, cinematic lighting, modern Chinese manhua web novel cover style, digital fantasy art, highly detailed, 8k resolution."
print(f"Today's Generated Prompt: {raw_prompt}")

# 4. Convert the prompt into a web-safe URL component
safe_prompt_path = quote(raw_prompt)

# 5. NEW OFFICIAL ENDPOINT PATTERN (/prompt/ replaces the broken legacy paths)
url = f"https://image.pollinations.ai/prompt/{safe_prompt_path}"

# 6. Set up image details cleanly
payload_parameters = {
    "width": 1024,
    "height": 1024,
    "model": "flux",
    "enhance": "true",
    "seed": random.randint(1, 999999)
}

print(f"Sending request to updated Pollinations API...")
response = requests.get(url, params=payload_parameters)

# 7. Create the folder and save the image with an exact timestamp
os.makedirs("generated_images", exist_ok=True)
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
file_path = f"generated_images/art_{timestamp_str}.jpg"

# 8. Check that the server actually sent back a proper image file, not error text
if response.status_code == 200 and b"html" not in response.content[:100]:
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"Successfully saved image to: {file_path}")
else:
    print(f"Error: API endpoint failed to return a valid image file. Status: {response.status_code}")
