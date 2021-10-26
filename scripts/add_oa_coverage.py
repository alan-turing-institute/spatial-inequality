"""
Add output area coverage to previously generated JSONs without output area coverage
"""

import json
from glob import glob
from pathlib import Path

import numpy as np
from tqdm import tqdm

from networks_multi_objs import get_multi_obj_inputs, get_pop_oa_coverage

data_dir = "data/networks/2021-10-19_105503"

meta_path = Path(data_dir, "meta.json")
with open(meta_path, "r") as f:
    meta = json.load(f)
opt_inputs = get_multi_obj_inputs(
    meta["lad20cd"],
    meta["objectives"][0],
    meta["population_groups"],
    meta.get("workplace_name", "workplace"),
)

network_paths = glob(str(Path(data_dir, "theta_*_nsensors_*_objs_*.json")))
for net_path in tqdm(network_paths):
    print(net_path)
    with open(net_path, "r") as f:
        networks = json.load(f)
    networks["oa_coverage"] = get_pop_oa_coverage(
        np.array(networks["sensors"]),
        opt_inputs,
        networks["lad20cd"],
        networks["theta"],
    ).tolist()

    with open(net_path, "w") as f:
        json.dump(networks, f)
