"""Builds one pak per weapon from recipes/mohen.json, each in its own release zip.

usage: python tools/build_split.py VERSION [NAMES_JSON] [RECIPE]
Needs Bladesmith importable (python -m bladesmith). NAMES_JSON is Bladesmith's bladesmith/data/names.json, for the
weapons' English names in the zip names. Output: dist/Mohen_<Weapon>_<VERSION>.zip, packed like the main zip.
"""
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
LEAKS = [b"C:\\Users", b"AppData", Path.home().name.encode()]  # anything from the build machine


def pack(pak_dir: Path, pak: str, out: Path) -> None:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for ext in (".pak", ".ucas", ".utoc"):
            data = (pak_dir / f"{pak}{ext}").read_bytes()
            found = [p for p in LEAKS + [p.decode().encode("utf-16-le") for p in LEAKS] if p.lower() in data.lower()]
            assert not found, f"{pak}{ext} contains {found}"
            zi = zipfile.ZipInfo(f"ProjectPBZ/Content/Paks/~mods/{pak}{ext}", date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type, zi.create_system, zi.external_attr = zipfile.ZIP_DEFLATED, 0, 0x20
            z.writestr(zi, data)


def main(version: str, names_json: str | None, recipe_name: str = "mohen") -> None:
    """recipe_name: mohen (zips in dist/) or mohen-trails-only (paks only, in dist/mohen-trails-only/<Weapon>/)."""
    recipe = json.loads((ROOT / "recipes" / f"{recipe_name}.json").read_text(encoding="utf-8"))
    loose = recipe_name != "mohen"
    names = json.loads(Path(names_json).read_text(encoding="utf-8")) if names_json else {}
    for w in recipe["weapons"]:
        key = w["base"]
        pak = f"zzz_zMohen_{key}_P"
        label = re.sub(r"[^A-Za-z0-9 ]", "", names.get(key, key)).title().replace(" ", "")
        out = DIST / f"Mohen_{label}_{version}.zip"
        if loose:
            out = DIST / recipe_name / names.get(key, key).replace(":", "")
        if out.exists() and (loose or out.stat().st_size > 1 << 20):  # built by an earlier, interrupted run
            continue
        one = {**recipe, "pak_name": pak, "weapons": [w]}
        rfile = DIST / "recipes" / recipe_name / f"{key}.json"
        rfile.parent.mkdir(parents=True, exist_ok=True)
        rfile.write_text(json.dumps(one, indent=1), encoding="utf-8")
        pak_dir = out if loose else DIST / "pak" / key
        subprocess.run([sys.executable, "-m", "bladesmith", "build", str(rfile), "-o", str(pak_dir)],
                       check=True, capture_output=True, cwd=ROOT)
        if not loose:
            pack(pak_dir, pak, out)
        print(f"{out.name}  {out.stat().st_size / 2**20:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, *sys.argv[3:4])
