from glob import glob
from typing import Union, Optional
from pathlib import Path
from jinja2 import Template
from markdown import markdown
from spineq.data_fetcher import lad20nm_to_lad20cd
from utils import get_config, get_figures_save_dir, get_objectives


def find_fig_path(match_name: str, fig_dir: Union[str, Path]) -> Optional[Path]:
    """Find the path to the first file matching the query `match_name` in the directory
    `fig_dir`.

    Parameters
    ----------
    match_name : str
        Filename to match (passed to glob.glob)
    fig_dir : Union[str, Path]
        Directory to search for the file in

    Returns
    -------
    Optional[Path]
        Path to the found file, or None if there are no matches
    """
    matches = glob(str(Path(fig_dir, match_name)))
    if not matches:
        return None
    match_filename = Path(matches[0]).name
    return Path(fig_dir.stem, match_filename)


def main():
    """
    Creates a formatted report including all the generated figures for a local auhtority
    and decriptions of what each figure shows (using the template reoprt_template.md).
    Both a Markdown (report.md) and HTML (report.html) version of the report are saved.
    """
    print("Generating formatted reports...")
    with open("report_template.md") as f:
        template = Template(f.read())

    config = get_config()
    fig_dir = get_figures_save_dir(config)
    report_dir = fig_dir.parent
    rel_fig_dir = fig_dir.stem

    la_name = config["la"]
    la_code = lad20nm_to_lad20cd(la_name)
    fig_density = Path(rel_fig_dir, "demographics_density.png")
    fig_importance = Path(rel_fig_dir, "demographics_importance.png")
    fig_coverage_vs_nsensors = Path(rel_fig_dir, "coverage_vs_nsensors.png")

    _, all_groups = get_objectives(config)
    total_pop_name = all_groups["pop_total"]["title"]
    fig_totalpop = find_fig_path("pop_total_theta*_nsensors*.png", fig_dir)
    children_name = all_groups["pop_children"]["title"]
    fig_children = find_fig_path("pop_children_theta*_nsensors*.png", fig_dir)
    older_name = all_groups["pop_elderly"]["title"]
    fig_older = find_fig_path("pop_elderly_theta*_nsensors*.png", fig_dir)
    work_name = all_groups["workplace"]["title"]
    fig_workers = find_fig_path("workplace_theta*_nsensors*.png", fig_dir)

    fig_urb_obs_sensors = find_fig_path("urb_obs_sensors_nsensors_*.png", fig_dir)
    fig_urb_obs_coverage_grid = find_fig_path(
        "urb_obs_coverage_grid_theta_*_nsensors_*.png", fig_dir
    )
    fig_urb_obs_coverage_diff_grid = find_fig_path(
        "urb_obs_coverage_difference_grid_theta_*_nsensors_*.png", fig_dir
    )
    fig_urb_obs_coverage_oa = find_fig_path(
        "urb_obs_coverage_oa_theta_*_nsensors_*.png", fig_dir
    )
    fig_urb_obs_coverage_diff_oa = find_fig_path(
        "urb_obs_coverage_difference_grid_theta_*_nsensors_*.png", fig_dir
    )
    all_threshold = config["figures"]["multi_objectives"]["all_coverage_threshold"]
    fig_all_above_threshold = find_fig_path(
        f"multiobj_theta*_*sensors_above{round(all_threshold * 100)}cov.png",
        fig_dir,
    )
    work_threshold = config["figures"]["multi_objectives"]["work_coverage_threshold"]
    fig_work_above_threshold = find_fig_path(
        f"multiobj_theta*_*sensors_workabove{round(work_threshold * 100)}cov.png",
        fig_dir,
    )
    fig_max_child_work_above_threshold = find_fig_path(
        "multiobj_wplace*_child*_theta*_*sensors.png", fig_dir
    )
    fig_coverage_above_uo = find_fig_path(
        "multiobj_theta*_*sensors_above_urbobs.png", fig_dir
    )
    fig_max_min_coverage = find_fig_path(
        "multiobj_compromise_theta*_*sensors_cov*.png", fig_dir
    )
    obj_1 = config["optimisation"]["two_objectives"]["objectives"][0]
    obj_2 = config["optimisation"]["two_objectives"]["objectives"][1]
    obj_1 = all_groups[obj_1]["title"]
    obj_2 = all_groups[obj_2]["title"]
    fig_obj1_vs_obj2 = find_fig_path("2obj_theta*_*sensors.png", fig_dir)
    fig_spectrum = find_fig_path("2obj_spectrum_theta*_*sensors.png", fig_dir)
    fig_width = config["report"]["fig_width"]

    filled_template = template.render(
        la_name=la_name,
        la_code=la_code,
        fig_density=fig_density,
        fig_importance=fig_importance,
        fig_coverage_vs_nsensors=fig_coverage_vs_nsensors,
        total_pop_name=total_pop_name,
        fig_totalpop=fig_totalpop,
        children_name=children_name,
        fig_children=fig_children,
        older_name=older_name,
        fig_older=fig_older,
        work_name=work_name,
        fig_workers=fig_workers,
        fig_urb_obs_sensors=fig_urb_obs_sensors,
        fig_urb_obs_coverage_grid=fig_urb_obs_coverage_grid,
        fig_urb_obs_coverage_diff_grid=fig_urb_obs_coverage_diff_grid,
        fig_urb_obs_coverage_oa=fig_urb_obs_coverage_oa,
        fig_urb_obs_coverage_diff_oa=fig_urb_obs_coverage_diff_oa,
        all_threshold=all_threshold,
        fig_all_above_threshold=fig_all_above_threshold,
        work_threshold=work_threshold,
        fig_work_above_threshold=fig_work_above_threshold,
        fig_max_child_work_above_threshold=fig_max_child_work_above_threshold,
        fig_coverage_above_uo=fig_coverage_above_uo,
        fig_max_min_coverage=fig_max_min_coverage,
        obj_1=obj_1,
        obj_2=obj_2,
        fig_obj1_vs_obj2=fig_obj1_vs_obj2,
        fig_spectrum=fig_spectrum,
        fig_width=fig_width,
    )

    with open(Path(report_dir, "report.md"), "w") as f:
        f.write(filled_template)

    html = markdown(filled_template)
    with open(Path(report_dir, "report.html"), "w") as f:
        f.write(html)
    print("Reports saved to", report_dir)


if __name__ == "__main__":
    main()
