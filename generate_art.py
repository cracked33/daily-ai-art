"""
generate_art.py
----------------
Generates one AI illustration per run by combining random Xianxia
(cultivation-fantasy) and cyberpunk elements into a detailed prompt, then
requests an image and saves it to generated_images/ with a timestamped
filename.

Two free backends are supported:
  1. Hugging Face Inference API (FLUX.1-schnell) — used automatically if
     an HF_TOKEN secret/env var is set. Generally sharper output than
     Pollinations' free tier.
  2. Pollinations.ai — used as a fallback if no HF_TOKEN is set, or if
     Hugging Face fails/rate-limits. Uses gen.pollinations.ai (with a
     POLLINATIONS_TOKEN, watermark-free) or the anonymous endpoint
     otherwise.

Both are free, keyless-by-default services with a real self-service
registration path for higher limits — no scraped cookies or bypassed
paywalls involved.
"""

import os
import random
import time
import urllib.parse
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# 1. PROMPT INGREDIENT LISTS
#    Expanded pools = far more unique combinations before anything repeats.
#    Feel free to add / edit / remove entries — the script adapts automatically.
# ---------------------------------------------------------------------------

CHARACTERS = [
    "a stern female sword cultivator", "a young rogue immortal cultivator",
    "an ancient dragon-blooded emperor", "a fox spirit hacker",
    "a blind oracle monk", "a rebel cyber-alchemist princess",
    "a disgraced sect elder", "a bio-engineered phoenix warrior",
    "a masked bounty-hunting nun", "a celestial swordsman turned outlaw",
    "a nine-tailed spirit fox in human form", "a scarred veteran demon hunter",
    "a child prodigy sword saint", "a cybernetic tiger-clan general",
    "an exiled crown prince turned wanderer", "a spectral assassin bound by an oath",
    "a jade-armored battle priestess", "a data-thief cultivator of the void sect",
    "a reincarnated star general", "a plague doctor turned qi healer",
]

OUTFITS = [
    "flowing silk hanfu robes fused with glowing circuit-thread embroidery",
    "black-and-gold cultivator armor lined with neon fiber-optic seams",
    "a tattered taoist robe patched with chrome cybernetic plating",
    "a high-collared battle cheongsam wired with holographic talismans",
    "ceremonial sect robes with a retractable exosuit frame underneath",
    "layered silk sashes threaded with liquid-metal circuitry",
    "a bone-white battle robe etched with luminous rune-code",
    "segmented obsidian armor plates over an inner silk lining",
    "a war-torn imperial cloak stitched with fiber-optic phoenix feathers",
    "translucent qi-channeling robes that shimmer like liquid glass",
    "a hooded assassin's wrap lined with retractable blade-talismans",
    "royal battle regalia fused with a servo-powered exosuit collar",
]

ACTIONS = [
    "unsheathing a blade wreathed in crackling spirit-energy",
    "channeling qi through both palms as neon sigils ignite midair",
    "meditating cross-legged atop a floating server-shrine",
    "leaping between shattered holographic pagodas",
    "forming hand seals that trigger a cascading data-storm",
    "standing defiant as lightning-forged talismans orbit her",
    "shattering a jade barrier with a single palm strike",
    "riding a surge of qi across a collapsing bridge of light",
    "summoning a spectral dragon coiled from streams of code",
    "locked mid-duel, blades sparking against a rune-shield",
    "kneeling before a shattered throne, qi coiling around clenched fists",
    "soaring above the skyline on a talisman-powered glider",
]

SCI_FI_ARRAYS = [
    "a massive glowing cultivation formation array rendered in circuit-board patterns",
    "a holographic bagua diagram spinning above a data-core altar",
    "concentric talisman rings pulsing like a quantum processor",
    "a shattered jade array leaking streams of binary code",
    "an ancient seal array overlaid with a targeting-HUD interface",
    "a towering array of interlocking gears and glowing rune-glyphs",
    "a spirit-formation collapsing into cascading streams of light-code",
    "twin dueling arrays clashing in a storm of golden sparks",
    "a dormant ancestral array reactivating with pulses of violet light",
]

LANDSCAPES = [
    "a mist-covered mountain sect rebuilt as a neon megacity skyline",
    "floating cultivation islands tethered by fiber-optic bridges",
    "a bamboo forest lit by drifting holographic lanterns and drones",
    "a ruined imperial palace fused with towering server spires",
    "a starlit spirit-lake reflecting a cyberpunk city skyline",
    "an ancient battlefield strewn with broken mechs and lotus blossoms",
    "a sky-piercing pagoda wrapped in cascading neon waterfalls",
    "an underground black market bazaar lit by lantern-drones",
    "a shattered heavenly gate suspended above a glowing metropolis",
    "an abandoned cultivation academy reclaimed by wild circuitry-vines",
    "a storm-wracked sea cliff beneath a fractured holographic moon",
]

MOODS = [
    "dramatic cinematic lighting", "moody neon rim lighting",
    "golden-hour god rays cutting through smog", "electric blue and crimson color palette",
    "soft bioluminescent glow", "high-contrast chiaroscuro lighting",
    "stormy backlighting with flickering neon reflections",
    "cool violet moonlight against warm ember sparks",
    "hazy volumetric fog lit by scattered holographic signage",
]

# Camera/finish details layered on top for extra render variety
CAMERA_DETAILS = [
    "low-angle heroic shot", "dynamic three-quarter view", "close-up dramatic portrait framing",
    "wide establishing shot with a small central figure", "over-the-shoulder cinematic framing",
]

QUALITY_BOOSTERS = [
    "intricate linework", "hyper-detailed textures", "masterful composition",
    "award-winning illustration", "razor-sharp focus", "painterly rendering",
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
        random.choice(CAMERA_DETAILS),
        random.choice(QUALITY_BOOSTERS),
        STYLE_SUFFIX,
    ]
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# 3a. BACKEND: HUGGING FACE INFERENCE API (FLUX.1-schnell)
#     Docs: https://huggingface.co/docs/api-inference
# ---------------------------------------------------------------------------

HF_MODEL_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"


def generate_image_huggingface(prompt: str, width: int = 1024, height: int = 1536,
                                max_retries: int = 3, timeout: int = 120) -> bytes:
    """
    Requests an image from Hugging Face's free Inference API.
    Returns raw image bytes, or raises an exception on failure.

    Requires HF_TOKEN to be set (a free token from https://huggingface.co/settings/tokens).
    The free serverless backend can return a 503 with an 'estimated_time' while
    the model spins up (cold start) — this is handled by waiting and retrying.
    """
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": width,
            "height": height,
        },
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[HF attempt {attempt}/{max_retries}] Requesting image...")
            response = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=timeout)

            if response.status_code == 503:
                # Model is cold-starting on HF's shared infrastructure.
                wait = 20
                try:
                    wait = int(response.json().get("estimated_time", 20)) + 2
                except Exception:
                    pass
                print(f"  -> model loading, waiting {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise ValueError(
                    f"Response was not an image (Content-Type: {content_type}). "
                    f"First 200 bytes: {response.content[:200]!r}"
                )
            return response.content
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  -> failed: {exc}")
            if attempt < max_retries:
                time.sleep(5 * attempt)

    raise RuntimeError(f"Hugging Face generation failed after {max_retries} attempts: {last_error}")


# ---------------------------------------------------------------------------
# 3b. BACKEND: POLLINATIONS.AI (fallback)
# ---------------------------------------------------------------------------

ANON_BASE = "https://image.pollinations.ai/prompt/"
AUTH_BASE = "https://gen.pollinations.ai/image/"


def generate_image_pollinations(prompt: str, width: int = 1024, height: int = 1536,
                                 max_retries: int = 3, timeout: int = 90) -> bytes:
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(0, 999_999_999)
    params = {"width": width, "height": height, "model": "flux", "nologo": "true", "seed": seed}

    headers = {"User-Agent": "Mozilla/5.0 (automated-art-bot)"}
    token = os.environ.get("POLLINATIONS_TOKEN")

    if token:
        params["key"] = token
        headers["Authorization"] = f"Bearer {token}"
        url = f"{AUTH_BASE}{encoded_prompt}?{urllib.parse.urlencode(params)}"
        print("Using registered Pollinations API key (gen.pollinations.ai, watermark-free tier).")
    else:
        url = f"{ANON_BASE}{encoded_prompt}?{urllib.parse.urlencode(params)}"
        print("No POLLINATIONS_TOKEN set — using anonymous tier (watermarked).")

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Pollinations attempt {attempt}/{max_retries}] Requesting image...")
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type:
                raise ValueError(
                    f"Response was not an image (Content-Type: {content_type}). "
                    f"First 200 bytes: {response.content[:200]!r}"
                )
            return response.content
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"  -> failed: {exc}")
            if attempt < max_retries:
                time.sleep(5 * attempt)

    raise RuntimeError(f"Pollinations generation failed after {max_retries} attempts: {last_error}")


# ---------------------------------------------------------------------------
# 3c. TOP-LEVEL DISPATCH: try Hugging Face first, fall back to Pollinations
# ---------------------------------------------------------------------------

def generate_image(prompt: str, width: int = 1024, height: int = 1536) -> bytes:
    if os.environ.get("HF_TOKEN"):
        try:
            return generate_image_huggingface(prompt, width, height)
        except Exception as exc:  # noqa: BLE001
            print(f"Hugging Face backend failed entirely ({exc}); falling back to Pollinations.")

    return generate_image_pollinations(prompt, width, height)


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
