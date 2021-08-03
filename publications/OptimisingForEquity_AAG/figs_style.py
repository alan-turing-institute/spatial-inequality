import matplotlib as mpl
import matplotlib.pyplot as plt


def set_fig_style():
    # fivethirtyeight style defaults but with white background
    plt.style.use("fivethirtyeight")
    mpl.rcParams["figure.facecolor"] = "white"

    mpl.rcParams["axes.facecolor"] = "white"
    mpl.rcParams["axes.grid"] = False

    mpl.rcParams["savefig.facecolor"] = "white"
