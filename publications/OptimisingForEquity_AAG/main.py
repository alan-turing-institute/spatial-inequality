from sensors_urb_obs import main as sensors_urb_obs
from networks_single_obj import main as networks_single_obj
from networks_multi_objs import main as networks_multi_objs
from figs_demographics import main as figs_demographics
from figs_single_obj import main as figs_single_obj
from figs_urb_obs import main as figs_urb_obs


def main():
    sensors_urb_obs()
    networks_single_obj()
    networks_multi_objs()
    figs_demographics()
    figs_single_obj()
    figs_urb_obs()


if __name__ == "__main__":
    main()
