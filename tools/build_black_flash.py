"""Black Sha-Chi flash: Soul's blue flash on a heavy attack with enough Sha-Chi, in black.

usage: python tools/build_black_flash.py OUT_DIR
Needs Bladesmith importable. Changes the game's own effect (NS_AttackAlertHun_Blue_001) at its path, so it works on
every weapon, with or without Mohen. Every material color of the effect goes near black and so does its color curve:
the glow fades and the smoke turns dark.
"""
import re
import sys
import tempfile
from pathlib import Path
from bladesmith import recolor, tools
from bladesmith.asset import Asset
from bladesmith.config import load
from bladesmith.game import Game
from bladesmith.recipe import Builder

PAK = sys.argv[2] if len(sys.argv) > 2 else "zzz_BlackShaChiFlash_P"
FX = "/PBZVFXPack/VFX/BlackShaChiFlash/MI"
BLACK = 0.02
g = Game(load())
src = g.resolve("NS_AttackAlertHun_Blue_001")
b = Builder(g, {}, Path(tempfile.mkdtemp()) / "stage")
raw = Asset(g.json_of(src, mapped=False))
mi_targets = {}
for i in raw.find_imports("MaterialInstanceConstant"):
    mi = raw.package_of(i)
    params = {}
    for d in Asset(g.json_of(mi)).main_data():
        if d.get("Name") == "VectorParameterValues":
            for el in d["Value"]:
                f = {x["Name"]: x for x in el["Value"]}
                name = next(x["Value"] for x in f["ParameterInfo"]["Value"] if x["Name"] == "Name")
                v = f["ParameterValue"]["Value"]
                if v and re.search(r"Colou?r|Tint|Emiss", name) and not re.search(r"Picker|Channel|Tiling|_ST", name):
                    params[name] = [BLACK, BLACK, BLACK, float(v[0]["Value"]["A"])]
    if params:
        dst = f"{FX}/{mi.rsplit('/', 1)[1]}"
        b.edited[dst] = (recolor.material_copy(g, mi, dst, params)[0], True)
        mi_targets[mi] = dst
        print(mi.rsplit("/", 1)[1], sorted(params))
eff = recolor.effect_copy(g, src, src, {"lut_gray": 0.0}, mi_targets)  # in place, its curve black too
b._add_copies([eff], {})
b.write()
utoc = Path(sys.argv[1]) / f"{PAK}.utoc"
utoc.parent.mkdir(parents=True, exist_ok=True)
tools.pack(g.cfg, b.stage, utoc)
print(utoc.with_suffix(".pak"))
