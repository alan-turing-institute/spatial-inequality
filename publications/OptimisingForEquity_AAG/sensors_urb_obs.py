import os
from pathlib import Path
import yaml
from spineq.data_fetcher import get_uo_sensors, lad20nm_to_lad20cd
from utils import get_config


def save_uo_sensors(lad20cd, save_path):
    uo_sensors = get_uo_sensors(lad20cd)
    uo_sensors.to_file(save_path)
    return uo_sensors


def add_n_uo_sensors_to_config(uo_sensors, config):
    n_uo_oa = uo_sensors["oa11cd"].nunique()
    if n_uo_oa not in config["optimisation"]["n_sensors"]["generate"]:
        print(
            f"Urban Observatory sensors found in {n_uo_oa} OA. "
            "Adding this to network sizes to generate."
        )
        n_sensors = config["optimisation"]["n_sensors"]["generate"]
        n_sensors.append(n_uo_oa)
        config["optimisation"]["n_sensors"]["generate"] = n_sensors
        with open("config.yml", "w") as f:
            return yaml.dump(config, f)


def main():
    config = get_config()
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    uo_dir = config["urb_obs"]["save_dir"]
    uo_name = config["urb_obs"]["filename"]
    save_path = Path(save_dir, lad20cd, uo_dir, uo_name)
    os.makedirs(save_path.parent, exist_ok=True)

    uo_sensors = save_uo_sensors(lad20cd, save_path)
    add_n_uo_sensors_to_config(uo_sensors, config)


if __name__ == "__main__":
    main()
