"""Writes recipes/mohen.json: ink trails on every weapon's attacks and a black blade on every weapon.

usage: python tools/make_recipe.py <Bladesmith's catalog JSON>
The catalog is Bladesmith's bladesmith/data/prebuilt.json (or its cached catalog.json): every player weapon
with its trail tags, read from your own copy of the game.
"""
import json
import sys
from pathlib import Path

# MoYuan's strong trail: a black brush stroke with a crimson edge and black ink drops, and it fades, so it suits
# every attack. (His basic trail has no drops, his charged one throws red sparks.)
INK = "NS_MoYuan_Trail_Strong_001"
# light attacks: the bandit JinYe's blood trail, black after the ink preset, so every combo shows both
SPLASH = "NS_JinYe_BloodTrail_101"
KEEP = ("Kick", "Blink")  # kicks and the dodge keep their own look
# the whole weapon: the brightest steel becomes this dark grey. "mesh": a copy of the blade mesh carries the
# material, since some blades (bleeding ones like Iron) rebuild it from the mesh and ignore the override
BLACK = {"to": "#383838", "all": True, "mesh": True}
# Double (the Sanguine Twins) draws no trails in the base game: its attacks draw them only for Jade weapons.
# Turning them on (the Jade tag, or Double added to that condition) crashes the game when the blades are drawn.
NO_BLADE = ("XieShan",)  # its blade is an effect, there is no material to recolor


def ink_for(tag: str) -> str | None:
    if tag.startswith(KEEP):
        return None
    return SPLASH if "A" in tag.split(".") else INK  # light attacks: the ink blood trail, the rest: the stroke


def recipe(catalog: list[dict]) -> dict:
    weapons = []
    for w in catalog:
        trails = {t["tag"]: ink_for(t["tag"]) for t in w["trails"] if ink_for(t["tag"])}
        entry = {"base": w["key"], "trails": trails, "trail_color": "presets/ink.json"}
        if not w["key"].startswith(NO_BLADE):
            entry["blade_color"] = BLACK
        weapons.append(entry)
    # small z: a mod that changes a weapon's look wins on that weapon
    return {"pak_name": "zzz_zMohen_P", "weapons": weapons}


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    catalog = data["catalog"] if isinstance(data, dict) else data
    out = Path(__file__).resolve().parents[1] / "recipes" / "mohen.json"
    out.write_text(json.dumps(recipe(catalog), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out.name, len(recipe(catalog)["weapons"]), "weapons")
