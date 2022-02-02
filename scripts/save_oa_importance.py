import pandas as pd

from spineq.optimise import calc_oa_weights
from spineq.plotting import plot_oa_importance

theta = 500

age_weights = pd.Series(0, index=range(91))
age_weights[age_weights.index >= 75] = 1
# age_weights = 1

population_weight = 1
workplace_weight = 0

vmin = None
vmax = None

save_dir = "/Users/jroberts/OneDrive - The Alan Turing Institute/UrbanObservatorySpatialInequality/AIUK/importance"

oa_weights = calc_oa_weights(
    lad20cd="E08000021",
    age_weights=age_weights,
    population_weight=population_weight,
    workplace_weight=workplace_weight,
)

plot_oa_importance(
    oa_weights,
    theta=theta,
    vmin=vmin,
    vmax=vmax,
    title="Adults >= 75 Years Old",
    save_path=save_dir + "/elderly75_theta_500.png",
)
