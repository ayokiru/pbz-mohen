"""Writes recipes/mohen.json: the ink trails on every weapon's attack trails.

usage: python tools/make_recipe.py <Bladesmith's catalog JSON>
The catalog is Bladesmith's bladesmith/data/prebuilt.json (or its cached catalog.json): every player weapon
with its trail tags, read from your own copy of the game.
"""
import json
import sys
from pathlib import Path

# MoYuan's trails: a black brush stroke with a crimson edge, and they fade, so they suit every weapon
INK = {
    "A": "NS_MoYuan_Trail_Basic_001",
    "B": "NS_MoYuan_Trail_Strong_001",
    "C": "NS_MoYuan_Trail_Charged_001",
}
KEEP = ("Kick", "Blink")  # kicks and the dodge keep their own look


def ink_for(tag: str) -> str | None:
    if tag.startswith(KEEP):
        return None
    for part in tag.split("."):
        if part in INK:
            return INK[part]
    return INK["A"]  # stabs, vortexes, tails and the like get the basic stroke


def recipe(catalog: list[dict]) -> dict:
    weapons = []
    for w in catalog:
        trails = {t["tag"]: ink_for(t["tag"]) for t in w["trails"] if ink_for(t["tag"])}
        if trails:
            weapons.append({"base": w["key"], "trails": trails})
    # small z: a mod that changes a weapon's look wins on that weapon
    return {"pak_name": "zzz_zMohen_P", "weapons": weapons}


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    catalog = data["catalog"] if isinstance(data, dict) else data
    out = Path(__file__).resolve().parents[1] / "recipes" / "mohen.json"
    out.write_text(json.dumps(recipe(catalog), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out.name, len(recipe(catalog)["weapons"]), "weapons")
