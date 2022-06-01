import figs_demographics
import figs_multi_convergence
import figs_multi_objs
import figs_single_obj
import figs_two_objs
import figs_urb_obs
import networks_multi_objs
import networks_random
import networks_single_obj
import networks_two_objs
import report
import sensors_urb_obs
from utils import make_results_dir


def main():
    """
    Run all scripts to process the data, generate optimised networks and save figures
    and a formatted report for a local authority, as defined by the parameters in
    `config.yml`.
    """
    make_results_dir()
    sensors_urb_obs.main()
    networks_single_obj.main()
    networks_multi_objs.main()
    networks_two_objs.main()
    networks_random.main()
    figs_demographics.main()
    figs_single_obj.main()
    figs_urb_obs.main()
    figs_multi_objs.main()
    figs_two_objs.main()
    figs_multi_convergence.main()
    report.main()


if __name__ == "__main__":
    main()
