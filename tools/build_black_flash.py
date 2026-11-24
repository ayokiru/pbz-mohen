"""Black Sha-Chi flash: Soul's blue Sha-Chi effects in black (the flash on a heavy attack, Sanguine's Sha-Chi dash
and its Chi-Infused Blade).

usage: python tools/build_black_flash.py OUT_DIR
Needs Bladesmith importable. Changes the game's own effects at their paths, so it works on every weapon, with or
without Mohen. Every material color of an effect goes near black, and so do its color curve and the blue colors baked
into its scripts: the glow fades and the smoke turns dark.
"""
import re
import struct
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
# effect -> blue colors baked into its scripts, as (r, g, b) floats, written near black too
TARGETS = {
    "NS_AttackAlertHun_Blue_001": [],                  # the flash on Soul's chest
    "NS_ShaQiEnd_001_Trail": [(0.2, 10.0, 25.0), (0.0, 0.501, 2.004)],  # the line of Sanguine's Sha-Chi dash (ShunSha)
    "NS_Weapon_Tang_ShunSha_BodyTrail_001": [],        # the dust behind that dash
    # Sanguine's Chi-Infused Blade (stance + heavy): the burst when it starts, the sparks and the glow on the blade
    "NS_HeiShang_TangChange_401": [(0.15, 1.0, 10.0), (0.25, 0.55, 3.0), (0.125, 0.501, 2.002)],
    "NS_Weapon_Tang_Blade_Spark_101": [(0.0, 0.129, 0.501)],
    "NS_Weapon_Tang_Blade_Spark_102": [(0.0, 0.129, 0.501)],
    "NS_Weapon_TangBuff_401": [],
}
b = Builder(g, {}, Path(tempfile.mkdtemp()) / "stage")
effects = []
for name, baked in TARGETS.items():
    src = g.resolve(name)
    raw = Asset(g.json_of(src, mapped=False))
    mi_targets = {}
    for i in raw.find_imports("MaterialInstanceConstant"):
        mi = raw.package_of(i)
        params = {}
        for d in Asset(g.json_of(mi)).main_data():
            if d.get("Name") == "VectorParameterValues":
                for el in d["Value"]:
                    f = {x["Name"]: x for x in el["Value"]}
                    pname = next(x["Value"] for x in f["ParameterInfo"]["Value"] if x["Name"] == "Name")
                    v = f["ParameterValue"]["Value"]
                    if v and re.search(r"Colou?r|Tint|Emiss", pname) and not re.search(r"Picker|Channel|Tiling|_ST", pname):
                        params[pname] = [BLACK, BLACK, BLACK, float(v[0]["Value"]["A"])]
        if params:
            dst = f"{FX}/{mi.rsplit('/', 1)[1]}"
            if dst not in b.edited:
                b.edited[dst] = (recolor.material_copy(g, mi, dst, params)[0], True)
            mi_targets[mi] = dst
    try:
        recolor.color_lut(g.json_of(src))
        spec = {"lut_gray": 0.0}  # its color curve black too
    except recolor.PresetError:
        spec = {}
    eff = recolor.effect_copy(g, src, src, spec, mi_targets)  # in place: the game spawns it by this path
    data = g.raw_bytes(src)
    for rgb in baked:
        # the exact floats behind the rounded values above
        hits = {data[o:o + 12] for o in range(0, len(data) - 12, 4)
                if all(abs(x - y) <= 1e-3 * max(1.0, abs(y)) for x, y in zip(struct.unpack_from("<3f", data, o), rgb))}
        assert hits, f"{name}: {rgb} not found"
        for h in hits:  # the same color can be stored with slightly different last bits
            eff.patches.append(recolor.BytePatch(f"{name} {rgb}", h, struct.pack("<3f", BLACK, BLACK, BLACK), every=True))
    effects.append(eff)
    print(name, sorted(m.rsplit("/", 1)[1] for m in mi_targets), spec, len(baked), "baked colors")
b._add_copies(effects, {})
b.write()
utoc = Path(sys.argv[1]) / f"{PAK}.utoc"
utoc.parent.mkdir(parents=True, exist_ok=True)
tools.pack(g.cfg, b.stage, utoc)
print(utoc.with_suffix(".pak"))
