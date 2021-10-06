import os
from pathlib import Path
import yaml
import geopandas as gpd
from spineq.data_fetcher import get_uo_sensors, lad20nm_to_lad20cd
from utils import get_config


def save_uo_sensors(lad20cd: str, save_path: Path) -> gpd.GeoDataFrame:
    """Get Urban Observatory sensors in a local authority and save them to file.

    Parameters
    ----------
    lad20cd : str
        Local authority code
    save_path : Path
        Path to save sensor data

    Returns
    -------
    gpd.GeoDataFrame
        Urban observatoy sensor locations
    """
    uo_sensors = get_uo_sensors(lad20cd)
    uo_sensors.to_file(save_path)
    return uo_sensors


def add_n_uo_sensors_to_config(uo_sensors: gpd.GeoDataFrame, config: dict):
    """Check how many output areas the Urban Observatory has a sensor in. If the config
    file doesn't specify to optimise a network with that many sensors, add it so it's
    possible to make a fair comparison later.

    Parameters
    ----------
    uo_sensors : gpd.GeoDataFrame
        Urban Observatory sensor locations from spineq.data_fetcher.get_uo_sensors()
    config : dict
        Config loaded by utils.get_config()
    """
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
            yaml.dump(config, f)


def main():
    """
    Save Urban Observatory sensor locations to the path specified by
    "save_dir" and "filename" in the "urb_obs" section of config.yml.
    """
    print("Getting Urban Observatory data...")
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
