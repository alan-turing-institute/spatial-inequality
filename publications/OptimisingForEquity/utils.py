import os
import pickle
from pathlib import Path
from typing import Any, List, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml

from spineq.data_fetcher import lad20nm_to_lad20cd


def get_config() -> dict:
    """Loads the configuration file specifying optimisation and figure parameters"""
    with open("config.yml") as f:
        return yaml.safe_load(f)


def set_fig_style():
    """Sets the matplotlib figure style to fivethirtyeight defaults but with a white
    background and no grid
    """
    plt.style.use("fivethirtyeight")
    mpl.rcParams["figure.facecolor"] = "white"
    mpl.rcParams["axes.facecolor"] = "white"
    mpl.rcParams["axes.grid"] = False
    mpl.rcParams["savefig.facecolor"] = "white"


def load_pickle(path: Union[Path, str]) -> Any:
    """Loads a pickle file

    Parameters
    ----------
    path : Union[Path, str]
        Path to pickle file

    Returns
    -------
    Any
        Loaded pickle file contents
    """
    with open(path, "rb") as f:
        return pickle.load(f)


def get_objectives(config: dict) -> Tuple[dict, dict]:
    """Get the parameters of the objectives specified in config

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Tuple[dict, dict]
        Parameters (min and max age) for each residential population objective, and
        names (keys) and longer descriptions (values) for all objectives.
    """
    population_groups = config["objectives"]["population_groups"]
    all_groups = dict(population_groups)
    all_groups["workplace"] = config["objectives"]["workplace"]
    return population_groups, all_groups


def get_default_optimisation_params(config: dict) -> Tuple[float, int]:
    """Get the default coverage distance (theta) and number of sensors to use when
    optimising networks and generating figures.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Tuple[float, int]
        Coverage distance (theta) and number of sensors.
    """
    theta = config["optimisation"]["theta"]["default"]
    n_sensors = config["optimisation"]["n_sensors"]["default"]
    return theta, n_sensors


def get_all_optimisation_params(config: dict) -> Tuple[List[float], List[int]]:
    """Get all coverage distances (thetas) and numbers of sensors to create optimised
    networks for.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Tuple[List[float], List[int]]
        Lists of coverage distances (theta) and numbers of sensors.
    """
    thetas = config["optimisation"]["theta"]["generate"]
    n_sensors = config["optimisation"]["n_sensors"]["generate"]
    return thetas, n_sensors


def get_la_save_dir(config: dict) -> Path:
    """Get the path to the parent directory to use for saving local authority results.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Path
        Directory to save local authority results to
    """
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    return Path(save_dir, lad20cd)


def get_networks_save_dir(config: dict) -> Path:
    """Get the path to the directory to save generated networks in.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Path
        Directory to save gernerated networks in
    """
    la_path = get_la_save_dir(config)
    networks_dir = Path(la_path, config["optimisation"]["networks_dir"])
    os.makedirs(networks_dir, exist_ok=True)
    return networks_dir


def get_figures_save_dir(config: dict) -> Path:
    """Get the path to the directory to save figures in.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Path
        Directory to save figures in
    """
    la_path = get_la_save_dir(config)
    figures_dir = Path(la_path, config["figures"]["save_dir"])
    os.makedirs(figures_dir, exist_ok=True)
    return figures_dir
