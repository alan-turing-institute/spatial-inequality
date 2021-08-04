import os
from pathlib import Path
import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
import yaml

from spineq.data_fetcher import lad20nm_to_lad20cd


def get_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)


def set_fig_style():
    # fivethirtyeight style defaults but with white background
    plt.style.use("fivethirtyeight")
    mpl.rcParams["figure.facecolor"] = "white"

    mpl.rcParams["axes.facecolor"] = "white"
    mpl.rcParams["axes.grid"] = False

    mpl.rcParams["savefig.facecolor"] = "white"


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def get_objectives(config):
    population_groups = config["objectives"]["population_groups"]
    all_groups = dict(population_groups)
    all_groups["workplace"] = config["objectives"]["workplace"]
    return population_groups, all_groups


def get_default_optimisation_params(config):
    theta = config["optimisation"]["theta"]["default"]
    n_sensors = config["optimisation"]["n_sensors"]["default"]
    return theta, n_sensors


def get_all_optimisation_params(config):
    thetas = config["optimisation"]["theta"]["generate"]
    n_sensors = config["optimisation"]["n_sensors"]["generate"]
    return thetas, n_sensors


def get_la_save_dir(config):
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    return Path(save_dir, lad20cd)


def get_networks_save_dir(config):
    la_path = get_la_save_dir(config)
    networks_dir = Path(la_path, config["optimisation"]["networks_dir"])
    os.makedirs(networks_dir, exist_ok=True)
    return networks_dir


def get_figures_save_dir(config):
    la_path = get_la_save_dir(config)
    figures_dir = Path(la_path, config["figures"]["save_dir"])
    os.makedirs(figures_dir, exist_ok=True)
    return figures_dir
