"""
generate_art.py
----------------
Generates one AI illustration per run by combining random Xianxia
(cultivation-fantasy) and cyberpunk elements into a detailed prompt, then
requests an image and saves it to generated_images/ with a timestamped
filename.

Two free backends are supported:
  1. Hugging Face Inference API (FLUX.1-schnell) — used automatically if
     an HF_TOKEN secret/env var is set.
  2. Pollinations.ai — used as a fallback if no HF_TOKEN is set, or if
     Hugging Face fails/rate-limits.

CHANGES IN THIS VERSION (quality fixes)
  - Prompt pools no longer contain words that make FLUX invent text
    ("rune-glyphs", "binary code", "HUD", "signage", "book cover", ...).
  - Actions favour one weapon / one hand to reduce anatomy and object errors.
  - Neon/glow wording is toned down and a single muted colour palette is
    picked per image, instead of every list pushing "neon".
  - SD-era "quality tokens" (award-winning, trending on, 4k) were removed;
    they push FLUX toward an over-processed look.
  - Optional saturation post-process (fail-safe: on ANY error the original
    image is saved untouched). Control it with environment variables:
        POSTPROCESS=0        -> disable it completely
        SATURATION=0.88      -> 1.0 = unchanged, lower = more muted
"""

import os
import random
import time
import urllib.parse
from datetime import datetime
from io import BytesIO

import requests

# Pillow is optional: if it is missing, post-processing is skipped and the
# script behaves exactly like before.
try:
    from PIL import Image, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    PIL_AVAILABLE = False

POSTPROCESS = os.environ.get("POSTPROCESS", "1") == "1"
SATURATION = float(os.environ.get("SATURATION", "0.88"))

# ---------------------------------------------------------------------------
# 1. PROMPT INGREDIENT LISTS
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

# Fewer "neon / circuit / rune-code" words: those drive both over-saturation
# and invented lettering.
OUTFITS = [
    "flowing silk hanfu robes with subtle glowing thread embroidery",
    "black-and-gold cultivator armor with thin luminous seams",
    "a tattered taoist robe patched with brushed-steel plating",
    "a high-collared battle cheongsam with embroidered cloud patterns",
    "ceremonial sect robes over a slim mechanical exosuit frame",
    "layered silk sashes threaded with fine metallic filaments",
    "a bone-white battle robe with engraved ornamental patterns",
    "segmented obsidian armor plates over an inner silk lining",
    "a war-torn imperial cloak with feather-shaped metallic plating",
    "translucent qi-channeling robes that shimmer like liquid glass",
    "a hooded assassin's wrap with slim concealed blades",
    "royal battle regalia with a servo-powered exosuit collar",
]

# Simpler poses: at most one weapon, at most one hand doing something
# complicated. (Removed: hand seals, crossed/dueling blades, "both palms".)
ACTIONS = [
    "drawing a single sword from its sheath, the blade wreathed in crackling spirit-energy",
    "raising one open palm as pale glowing sigils gather in the air",
    "meditating cross-legged atop a floating shrine",
    "leaping between shattered pagoda rooftops",
    "standing defiant with one sword resting point-down, paper charms orbiting her",
    "shattering a jade barrier with a single palm strike",
    "riding a surge of qi across a collapsing bridge of light",
    "summoning a spectral dragon coiled from streams of light",
    "holding one sword in a ready stance behind a glowing shield of light",
    "kneeling before a shattered throne, qi coiling around clenched fists",
    "soaring above the skyline on a gliding disc of light",
    "walking calmly through drifting fog with one hand on a sword hilt",
]

# Renamed in spirit from "arrays" to "formations"; anything that reads like
# writing (code, HUD, glyphs, diagrams) was replaced with abstract patterns.
SCI_FI_ARRAYS = [
    "a massive glowing cultivation formation made of concentric circular patterns",
    "a spinning holographic ring of geometric patterns above an altar",
    "concentric glowing rings pulsing like a quantum processor",
    "a shattered jade ring leaking streams of light particles",
    "an ancient seal formation overlaid with faint targeting rings",
    "a towering structure of interlocking gears and glowing geometric carvings",
    "a spirit formation collapsing into cascading streams of light",
    "twin circular formations clashing in a storm of golden sparks",
    "a dormant ancestral formation reactivating with pulses of soft violet light",
]

LANDSCAPES = [
    "a mist-covered mountain sect rebuilt as a glittering megacity skyline",
    "floating cultivation islands tethered by fiber-optic bridges",
    "a bamboo forest lit by drifting holographic lanterns and drones",
    "a ruined imperial palace fused with towering server spires",
    "a starlit spirit-lake reflecting a distant city skyline",
    "an ancient battlefield strewn with broken mechs and lotus blossoms",
    "a sky-piercing pagoda wrapped in cascading luminous waterfalls",
    "an underground night bazaar lit by floating paper lanterns",
    "a shattered heavenly gate suspended above a glowing metropolis",
    "an abandoned cultivation academy reclaimed by wild circuitry-vines",
    "a storm-wracked sea cliff beneath a fractured glowing moon",
]

MOODS = [
    "dramatic cinematic lighting", "soft neon rim lighting on the edges only",
    "golden-hour god rays cutting through smog", "soft bioluminescent glow",
    "high-contrast chiaroscuro lighting",
    "stormy backlighting with faint reflections",
    "cool moonlight against warm ember sparks",
    "hazy volumetric fog lit by distant lights",
]

# One restrained palette per image instead of "electric blue and crimson".
COLOR_PALETTES = [
    "muted teal and warm ochre color palette",
    "desaturated jade green and charcoal palette with a single crimson accent",
    "cool slate-blue and soft gold color palette",
    "warm ember orange and deep indigo palette, soft and natural",
    "pale moonlit silver and deep teal color palette",
    "earthy sepia and faded vermilion color palette",
    "dark low-saturation surroundings with restrained neon accents",
]

CAMERA_DETAILS = [
    "low-angle heroic shot", "dynamic three-quarter view", "close-up dramatic portrait framing",
    "wide establishing shot with a small central figure", "over-the-shoulder cinematic framing",
]

FINISH_DETAILS = [
    "clean linework", "detailed but uncluttered", "balanced composition",
    "painterly rendering", "crisp edges", "refined illustration",
]

# Removed: "book cover", "web novel", "trending on ...", "4k concept art",
# "ultra detailed". "Cover" wording invites title text; the rest pushes an
# over-processed look.
STYLE_SUFFIX = (
    "digital fantasy illustration in a manhua style, one central figure, "
    "correct anatomy, five fingers on each hand, soft natural color grading, "
    "uncluttered background, vertical composition"
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
        random.choice(COLOR_PALETTES),
        random.choice(CAMERA_DETAILS),
        random.choice(FINISH_DETAILS),
        STYLE_SUFFIX,
    ]
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# 3a. BACKEND: HUGGING FACE INFERENCE API (FLUX.1-schnell)  [unchanged]
# ---------------------------------------------------------------------------

HF_MODEL_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"


def generate_image_huggingface(prompt: str, width: int = 1024, height: int = 1536,
                                max_retries: int = 3, timeout: int = 120) -> bytes:
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
# 3b. BACKEND: POLLINATIONS.AI (fallback)  [unchanged]
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
# 3c. TOP-LEVEL DISPATCH  [unchanged]
# ---------------------------------------------------------------------------

def generate_image(prompt: str, width: int = 1024, height: int = 1536) -> bytes:
    if os.environ.get("HF_TOKEN"):
        try:
            return generate_image_huggingface(prompt, width, height)
        except Exception as exc:  # noqa: BLE001
            print(f"Hugging Face backend failed entirely ({exc}); falling back to Pollinations.")

    return generate_image_pollinations(prompt, width, height)


# ---------------------------------------------------------------------------
# 3d. OPTIONAL POST-PROCESS: tone down over-saturation (fail-safe)
# ---------------------------------------------------------------------------

def soften_saturation(image_bytes: bytes, saturation: float = SATURATION) -> bytes:
    """
    Returns JPEG bytes with saturation scaled by `saturation` (1.0 = unchanged).
    If Pillow is missing or anything at all goes wrong, the ORIGINAL bytes are
    returned, so this step can never stop an image from being saved.
    """
    if not PIL_AVAILABLE:
        print("Pillow not installed; skipping color post-process.")
        return image_bytes
    try:
        im = Image.open(BytesIO(image_bytes)).convert("RGB")
        im = ImageEnhance.Color(im).enhance(saturation)
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except Exception as exc:  # noqa: BLE001
        print(f"Post-process failed ({exc}); keeping original image.")
        return image_bytes


# ---------------------------------------------------------------------------
# 4. SAVE THE IMAGE WITH A TIMESTAMPED FILENAME  [unchanged]
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

    if POSTPROCESS:
        image_bytes = soften_saturation(image_bytes)

    filepath = save_image(image_bytes)

    print(f"Saved image to: {filepath}")
    print(f"File size: {len(image_bytes) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
