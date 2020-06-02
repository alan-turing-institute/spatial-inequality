import pandas as pd

from .data_fetcher import get_oa_centroids, get_oa_stats, get_traffic_counts


def calc_location_weights(
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    traffic_weight=0,
    combine=True,
):
    """Calculate weighting factor for each location (output areas and traffic
    intersections).
    
    Keyword Arguments:        
        population_weight {float} -- Weighting for residential population
        (default: {1})
        
        workplace_weight {float} -- Weighting for workplace population
        (default: {0})
        
        pop_age_groups {dict} -- Residential population age groups to create
        objectives for and their corresponding weights. Dict with objective
        name as key. Each entry should be another dict with keys min (min age
        in population group), max (max age in group), and weight (objective
        weight for this group).
        
        traffic_weight {float} -- Weighting for traffic intersections.
        
        combine {bool} -- If True combine all the objectives weights into a
        single overall weight using the defined weighting factors. If False
        treat all objectives separately, in which case all weights defined in
        other parameters are ignored.
    
    Returns:
        pd.DataFrame or pd.Series -- Weight for each OA (indexed by oa11cd) for
        each objective. Series if only one objective defined or combine is True.
    """

    data = get_oa_stats()
    population_ages = data["population_ages"]
    workplace = data["workplace"]

    all_weights = None
    
    if len(population_ages) != len(workplace):
        raise ValueError(
            "Lengths of inputs don't match: population_ages={}, workplace={}".format(
                len(population_ages), len(workplace)
            )
        )

    # weightings for residential population by age group
    if population_weight > 0:
        oa_population_group_weights = {}
        for name, group in pop_age_groups.items():
            # skip calculation for zeroed objectives
            if group["weight"] == 0:
                continue

            # get sum of population in group age range
            group_population = population_ages.loc[
                :,
                (population_ages.columns >= group["min"])
                & (population_ages.columns <= group["max"]),
            ].sum(axis=1)

            # normalise total population
            group_population = group_population / group_population.sum()

            # if objectives will be combined, scale by group weight
            if combine:
                group_population = group_population * group["weight"]

            oa_population_group_weights[name] = group_population

        if len(oa_population_group_weights) > 0:
            use_population = True  # some population groups with non-zero weights

            oa_population_group_weights = pd.DataFrame(oa_population_group_weights)
            if combine:
                oa_population_group_weights = oa_population_group_weights.sum(axis=1)
                oa_population_group_weights = population_weight * (
                    oa_population_group_weights / oa_population_group_weights.sum()
                )
                oa_population_group_weights.name = "population"
                
            if all_weights is None:
                all_weights = pd.DataFrame(oa_population_group_weights)
            else:
                all_weights = pd.DataFrame(all_weights).join(oa_population_group_weights, how="outer")
        else:
            use_population = False  #  all population groups had zero weight
    else:
        use_population = False

    # weightings for number of workers in OA (normalised to sum to 1)
    if workplace_weight > 0:
        use_workplace = True
        workplace = workplace / workplace.sum()
        if combine:
            workplace = workplace_weight * workplace
        workplace.name = "workplace"
        
        if all_weights is None:
            all_weights = pd.DataFrame(workplace)
        else:
            all_weights = pd.DataFrame(all_weights).join(workplace, how="outer")
    else:
        use_workplace = False

    # weightings for traffic intersections
    if traffic_weight > 0:
        use_traffic = True
        traffic = get_traffic_counts()["traffic_co"]
        traffic = traffic / traffic.sum()
        traffic.name = "traffic"
        if combine:
            traffic = traffic_weight * traffic
            
        if all_weights is None:
            all_weights = pd.DataFrame(traffic)
        else:
            all_weights = pd.DataFrame(all_weights).join(traffic, how="outer")
    else:
        use_traffic = False
            
    if not use_population and not use_workplace and not use_traffic:
        raise ValueError("Must specify at least one non-zero weight.")

    # Some objectives may not have values for all stats (e.g. population at a
    # traffic intersection) - fill missing values with zeroes.
    all_weights = all_weights.fillna(0)
    
    if len(all_weights.columns) == 1:
        return all_weights[all_weights.columns[0]]
    elif combine:
        all_weights = all_weights.sum(axis=1)
        return all_weights / all_weights.sum()
    else:
        return all_weights