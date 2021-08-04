import matplotlib as mpl
import matplotlib.pyplot as plt
import pickle
import yaml


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
