"""Mutation controls for the fixed-codebook packing checker."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fixed_codebook_check import check_certificate  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
spec = json.loads((ROOT / "inputs" / "fixed-codebooks.json").read_text())[0]
base = json.loads((ROOT / "results" / "fixed-codebook" / "X01.json").read_text())


def rejected(name: str, mutate) -> dict:
    value = copy.deepcopy(base)
    mutate(value)
    try:
        check_certificate(spec, value)
    except Exception as error:
        return {"name": name, "passed": True, "rejection": str(error)}
    return {"name": name, "passed": False, "rejection": "mutation accepted"}


controls = [
    rejected("drop-packing-cell", lambda x: x["bounds"][1]["decoder_plane"]["packing"].pop()),
    rejected("duplicate-packing-cell", lambda x: x["bounds"][1]["decoder_plane"]["packing"].append(x["bounds"][1]["decoder_plane"]["packing"][0])),
    rejected("mutate-circuit-cube", lambda x: x["bounds"][1]["decoder_plane"]["terms"][0].update(cube="*****")),
    rejected("zero-output-mask", lambda x: x["encoder_plane"]["terms"][0].update(outputs=0)),
    rejected("drop-frontier-point", lambda x: x["frontier"].pop()),
    rejected("alter-encoder-row", lambda x: x["encoder_rows"].__setitem__(0, x["encoder_rows"][1])),
    rejected("understate-minimum", lambda x: x["bounds"][1]["decoder_plane"].update(minimum_products=4)),
    rejected("alter-forced-zero-set", lambda x: x["bounds"][2]["decoder_plane"]["forced_zero_cells"].pop()),
]

if not all(item["passed"] for item in controls):
    raise SystemExit("a fixed-codebook mutation was accepted")
out = {"passed": len(controls), "controls": controls}
path = ROOT / "results" / "fixed-codebook" / "controls.json"
path.write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
