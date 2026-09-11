"""
generate_art.py
----------------
Generates one AI illustration per run by combining random Xianxia
(cultivation-fantasy) and cyberpunk elements into a detailed prompt, then
requests an image from Pollinations.ai's free, keyless image API (Flux
model) and saves it to generated_images/ with a timestamped filename.

No API key, login, or cookie of any kind is required or used. This script
only calls Pollinations' public free endpoint as documented at
https://pollinations.ai — it does not attempt to access any paid tier.
"""

import os
import random
import time
import urllib.parse
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# 1. PROMPT INGREDIENT LISTS
#    Feel free to add / edit / remove entries in any list below — the script
#    will automatically pick from whatever is there.
# ---------------------------------------------------------------------------

CHARACTERS = [
    "a stern female sword cultivator", "a young rogue immortal cultivator",
    "an ancient dragon-blooded emperor", "a fox spirit hacker",
    "a blind oracle monk", "a rebel cyber-alchemist princess",
    "a disgraced sect elder", "a bio-engineered phoenix warrior",
    "a masked bounty-hunting nun", "a celestial swordsman turned outlaw",
]

OUTFITS = [
    "flowing silk hanfu robes fused with glowing circuit-thread embroidery",
    "black-and-gold cultivator armor lined with neon fiber-optic seams",
    "a tattered taoist robe patched with chrome cybernetic plating",
    "a high-collared battle cheongsam wired with holographic talismans",
    "ceremonial sect robes with a retractable exosuit frame underneath",
    "layered silk sashes threaded with liquid-metal circuitry",
]

ACTIONS = [
    "unsheathing a blade wreathed in crackling spirit-energy",
    "channeling qi through both palms as neon sigils ignite midair",
    "meditating cross-legged atop a floating server-shrine",
    "leaping between shattered holographic pagodas",
    "forming hand seals that trigger a cascading data-storm",
    "standing defiant as lightning-forged talismans orbit her",
]

SCI_FI_ARRAYS = [
    "a massive glowing cultivation formation array rendered in circuit-board patterns",
    "a holographic bagua diagram spinning above a data-core altar",
    "concentric talisman rings pulsing like a quantum processor",
    "a shattered jade array leaking streams of binary code",
    "an ancient seal array overlaid with a targeting-HUD interface",
]

LANDSCAPES = [
    "a mist-covered mountain sect rebuilt as a neon megacity skyline",
    "floating cultivation islands tethered by fiber-optic bridges",
    "a bamboo forest lit by drifting holographic lanterns and drones",
    "a ruined imperial palace fused with towering server spires",
    "a starlit spirit-lake reflecting a cyberpunk city skyline",
    "an ancient battlefield strewn with broken mechs and lotus blossoms",
]

MOODS = [
    "dramatic cinematic lighting", "moody neon rim lighting",
    "golden-hour god rays cutting through smog", "electric blue and crimson color palette",
    "soft bioluminescent glow", "high-contrast chiaroscuro lighting",
]

STYLE_SUFFIX = (
    "digital manhua web novel cover illustration, ultra detailed, "
    "sharp linework, dynamic pose, trending on manhua platforms, "
    "vertical book cover composition, 4k concept art"
)

# ---------------------------------------------------------------------------
# 2. BUILD A RANDOM PROMPT
# ---------------------------------------------------------------------------

def build_prompt() -> str:
    parts = [
        random.choice(CHARACTERS),
        "wearing " + random.choice(OUTFITS),
        random.choice(ACTIONS),
        "in front of " + random.choice(SCI_FI_ARRAYS),
        "set in " + random.choice(LANDSCAPES),
        random.choice(MOODS),
        STYLE_SUFFIX,
    ]
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# 3. CALL THE FREE POLLINATIONS.AI IMAGE ENDPOINT
#    Docs: https://pollinations.ai  (no API key needed for this endpoint)
# ---------------------------------------------------------------------------

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


def generate_image(prompt: str, width: int = 1024, height: int = 1536,
                    max_retries: int = 3, timeout: int = 90) -> bytes:
    """
    Requests an image for the given prompt and returns the raw image bytes.
    Retries on transient failures (the free endpoint occasionally times out
    under load, especially the first request after it's been idle).

    If a POLLINATIONS_TOKEN environment variable is set (populated from the
    POLLINATIONS_TOKEN GitHub secret), it's sent as a Bearer token. This is a
    token you generate yourself for free at https://auth.pollinations.ai —
    it unlocks the registered "Seed" tier, which removes the watermark and
    raises the rate limit. Nothing happens differently if it's not set; the
    script just falls back to the anonymous tier (watermarked, slower).
    """
    # urllib.parse.quote() safely encodes spaces, commas, punctuation, etc.
    # This is what prevents the "LocationParseError" / malformed-URL issue —
    # it's a plain URL-encoding fix, nothing exotic required.
    encoded_prompt = urllib.parse.quote(prompt)

    seed = random.randint(0, 999_999_999)
    params = {
        "width": width,
        "height": height,
        "model": "flux",     # free, high-quality model tier on Pollinations
        "nologo": "true",    # honored automatically once authenticated
        "seed": seed,
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{POLLINATIONS_BASE}{encoded_prompt}?{query_string}"

    headers = {"User-Agent": "Mozilla/5.0 (automated-art-bot)"}
    token = os.environ.get("POLLINATIONS_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("Using registered Pollinations token (watermark-free tier).")
    else:
        print("No POLLINATIONS_TOKEN set — using anonymous tier (watermarked).")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[attempt {attempt}/{max_retries}] Requesting image...")
            response = requests.get(
                url,
                timeout=timeout,
                headers=headers,
            )
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise ValueError(
                    f"Response was not an image (Content-Type: {content_type}). "
                    f"First 200 bytes: {response.content[:200]!r}"
                )
            return response.content
        except Exception as exc:  # noqa: BLE001 - we want to catch & retry broadly here
            last_error = exc
            print(f"  -> failed: {exc}")
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"  -> retrying in {wait}s...")
                time.sleep(wait)

    raise RuntimeError(f"Image generation failed after {max_retries} attempts: {last_error}")


# ---------------------------------------------------------------------------
# 4. SAVE THE IMAGE WITH A TIMESTAMPED FILENAME
# ---------------------------------------------------------------------------

def save_image(image_bytes: bytes, output_dir: str = "generated_images") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"art_{timestamp}.jpg"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------

def main():
    prompt = build_prompt()
    print(f"Generated prompt:\n{prompt}\n")

    image_bytes = generate_image(prompt)
    filepath = save_image(image_bytes)

    print(f"Saved image to: {filepath}")
    print(f"File size: {len(image_bytes) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
