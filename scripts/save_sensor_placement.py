from spineq.optimise import optimise

theta = 500
n_sensors = 60


# age_weights = pd.Series(0, index=range(91))
# age_weights[age_weights.index >= 75] = 1
age_weights = 1

population_weight = 0
workplace_weight = 1

optimise(
    theta=theta,
    n_sensors=n_sensors,
    age_weights=age_weights,
    population_weight=population_weight,
    workplace_weight=workplace_weight,
    save_result=True,
    save_plots="all",
    run_name="workplace",
    save_dir="~/Desktop",
    fill_oa=False,
    sensor_size=64,
    sensor_color="red",
    sensor_edgecolor="red",
)
