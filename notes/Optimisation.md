
# Optimisation

# References

- Cambridge paper

# Coverage

## Current Approach

- Currently have a coverage measure that covers an area of 500 metre radius (with default values).
- Coverage value applies to whole output area - if output area has a sensor the whole area is 100% covered.
- Considering coverage to extend over a large area results in a preference for networks with sensors evenly distributed around the whole city.

## Challenges/Issues
- Actual coverage area of a sensor, as in distance over which air quality measurement is relevant, is more like 50 metres.
- Coverage distance is not a constant - depends on road canyons, wind direction etc. Seen one paper that considers coverage only to extend along the road (not jump into neighbouring roads).
- If coverage changed to be a smaller area, need to add an additional constraint/objective for preferring sensors to be placed in all parts of the city.
- How to combine area- and point-based data? E.g. placing sensor at a school in an output area will give some coverage of the residential population in that area. And placing a sensor at an output area centroid doesn't really cover all the output area's residents.

# Sensor Sites

Options:
- Only place sensors at points of interest (e.g. at school or at output area centroid)
  - Pros: Guarantees sensor to be in an interesting location. Reduces number of possible solutions.
  - Cons: May miss interesting compromise locations. May limit algorithm options.
- Lampposts
  - Pros: Sensors can typically be placed on lampposts.
  - Cons: Many more lampposts than points of interest (will take longer) without obvious benefits.
- Arbitrary positions (then move to nearest realistic location afterwards?)
  - Pros: May give more options in terms of choice of optimisation algorithm.
  - Cons: May result in undesirable compromises (e.g. sensor halfway between two schools).

# Objective

### Weightings

- How to select in a meaningful way in the optimisation backend?
- How to present in an intuitive way to the user in the frontend?

### Combining Objectives

Options:
- One multi-objective optimisation. Each objective has a weighting and we create a single network optimised for those weightings.
  - Pros: Only need to run one optimisation. Will find good compromise locations, e.g. likely to pick locations that are 2nd best for each individual objective.
  - Cons: Maybe less intuitive for decision support tool. Effect of weightings less clear.
- Separate optimisation for each objective. Weight each objective by assigning a different number of sensors to each one.
  - Pros: Nice way to compare good locations for each objective.
  - Cons: Need to run a separate (simpler) optimisation for each objective. May miss compromise locations, e.g. prefer picking a location ranked 1st for one objective than one ranked 2nd for many objectives.

### Equality

- Rather than (or as well as) having a preference for sensors to be evenly distributed throughout the city, we may want to have terms to force an even coverage of demographics, e.g. similar number of sensors for each IMD decile.


# Constraints

Number of sensors

# Algorithm

- Currently a "homemade" greedy algorithm.


# Considerations for User Interface

### Complexity

### Speed

- A typical user of the decision support tool may not be willing to wait more than a few minutes for a result.
  - Who is the typical user - member of public may only wait minutes, policy maker may be willing to wait a day.
- Adding complexity adds computation time - definitely feasible that it could take closer to hours than minutes.
- What can we provide within a few seconds?


# Libraries

## Genetic Algorithms

* PyGMO

* pymoo

## Others

* scipy

* pytorch
