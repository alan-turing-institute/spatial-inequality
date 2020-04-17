
# Optimisation

To define and run an optimisation for generating a network of sensors we need:
- A set of possible sensor locations.
- A concept of coverage - to what extent do the areas neighbouring a sensor benefit?
- An objective, or a set of objectives, to maximise.
- A set of constraints - conditions that must be met for a solution to be viable.
- An algorithm to pick the best sensor locations to maximise the objective.

# Sensor Sites

There are three broad options for the set of locations to input as the set of possible sensor sites:

1) Only place sensors at points of interest (e.g. at a school or at an output area centroid):
  - Pros: Guarantees sensor to be in an interesting location. Reduces number of possible solutions.
  - Cons: May miss interesting compromise locations. May limit algorithm options.
2) Lampposts (or any other discrete set of points that is different to the points of interest):
  - Pros: Sensors can typically be placed on lampposts.
  - Cons: Many more lampposts than points of interest (will take longer) without obvious benefits for the resulting network.
3) Arbitrary positions (in continuous space rather than discrete points):
  - Pros: May give more options in terms of choice of optimisation algorithm.
  - Cons: May result in undesirable compromises (e.g. sensor halfway between two schools) or infeasible locations (but could snap to nearest viable site afterwards).

Variations of all three are found (or at least discussed) in the literature, including the Cambridge paper.

## Current Approach

The optimisation currently uses option 1 above - the set of sensor sites considered is the same as the points of interest (output area population weighted centroids). I think this makes the most sense for our current inputs - as our stats apply to whole output areas it would seem dubious to make any claims about where sensors should be placed at a higher granularity than output areas (e.g. there's no way we can justify that a lamppost is better than the one next to it).

When we add other inputs, such as hospital or traffic intersection locations, the natural extension would be to simply add those as possible sensor sites also.

## Alternatives

- David has code (in the `sensor_sites` directory in this repo) to generate sets of points based on lamppost locations, an even grid etc. Minor modifications to the optimisation code would allow these to be used as sensor sites instead -  `spnieq.optimise:get_optimisation_inputs` would need to return a list of sensor x and y locations, which should then be passed to `coverage_matrix` as the `x2` and `y2` arguments (with `x1` and `y1` still output area centroids). The length of the `sensors` array would need to be changed to the number of sensor sites instead of the number of points of interest, also.

- I have briefly played with arbitrary sensor locations (approach 3) in the _"PyGMO: Sensors at any arbitrary position"_ and _"SciPy optimize"_ sections of the `notebooks/population_optimisation.ipynb` notebook.


# Coverage

Each sensor that is placed gives "coverage" of a certain area. In my opinion, there are three different coverage concepts, each with different merits. These are:

1) Distance over which a sensor is expected to give an accurate measurement (i.e. how far away can I stand from a sensor and still be confident that the quality of air I'm breathing in is similar to the sensor's measurement?) This distance seems to be tens of metres (maybe 30-50 metres).

2) Whether a region/part of the city contains a sensor. This is relevant for questions such as whether a network gives a representative sample of all the different environments in the city, and whether members of the public feel as though the local government is taking sufficient interest in their area. The distance scale here is maybe the size of a neighbourhood, or hundreds of metres.

3) Required density or distribution of sensors to be able to create an accurate air quality model for the whole city, i.e. whether placing a sensor in a given location will lead to a significant improvement in a model's predictions.

Concept 3 is particularly relevant for air quality modelling, whereas Concept 2 is perhaps more relevant for social or political policy decisions. Concept 1 has relevance for both, but in particular prioritises coverage of individuals (or small areas) as opposed to coverage of (larger) areas.

## Current Approach

The coverage concept we've used so far is most like concept 2 above. This is motivated by factors such as:

- We'd like our work to be applicable to cities without a pre-existing sensor network or air quality model.
- There will be a relatively small number of sensors (compared to the size of the population/the size of the city).
- The focus of the project isn't air quality modelling and developing a model for Newcastle would be a significant time investment (even if building on previous work).
- The focus of the project is coverage of population, or coverage of under-represented demographics.

Our "coverage" metric is inspired by the population "satisfaction" metric in the Cambridge paper. They claim (or approximate) that the level of satisfaction a member of the public has with a given sensor network is dependent only on the distance between their place of residence and the nearest sensor.

They use an exponential decay (justified for its mathematical properties rather than any claim on how distance determines actual satisfaction, I think), defined as:

$C = \exp(-d/\theta)$

Where $C$ is the coverage at a point, $d$ is the distance between that point and the nearest sensor, and $\theta$ is a decay rate parameter (large $\theta$ values mean coverage extends over a larger distance). Coverage equals 1 (or 100%) if a sensor is placed at the point of interest, or 1/e (0.37) if the nearest sensor is $\theta$ metres away.

The Cambridge paper uses a value of $\theta = 1000$ metres (I believe), which is the size of grids in the population data they use (they don't justify this value beyond that). We have used a default value of $\theta = 500$ metres so far, which makes the coverage as a function of distance look like this:
![](figs/coverage.png)

Large theta values (I would consider 500 metres to be large) lead to a preference for networks with sensors evenly distributed around the whole city. Small theta values (say 100 metres) lead to a preference for sensors to be placed in areas of high density/interest, even if they are all clustered in the same part of the city.

## Implementation

So far our optimisation has used output area centroids both as possible sensor sites and as points of interest for coverage. There are around 1000 output areas (more like 950). I've taken the approach of pre-computing the coverage values (coverage at any output area due to a sensor placed at any other output area), creating a ~1000 x 1000 matrix. This takes a few seconds (probably could be made quicker) but avoids having to recalculate values during the optimisation.

The relevant functions are in `spineq/utils.py` and rely on array operations in `numpy`. The steps are:
1) Calculate pairwise distances between output area centroids (distance between each centroid and all the other centroids). Function: `distance_matrix`.
2) Convert the distances into coverage values using the exponential decay equation above. Function: `coverage_matrix`.

To calculate the coverage at an output area given a sensor network (with an arbitrary number of sensors), the process (currently in `spineq/optimise.py:optimise`) is:
1) Make an array (of length n_output_areas) which is 1 if a location has a sensor, and 0 otherwise.
2) Extract the output area's row from the coverage matrix.
3) Multiply the output area coverage values by the sensor array - leaves only coverage values due to locations that have a sensor.
4) Take the max of the remaining coverage values - this is the output area coverage with the given sensor network.

## Challenges/Issues

- So far we have considered only output area stats and sensors placed at output area centroids. If an output area has a sensor at its centroid we consider the whole output area to be 100% covered. This is clearly not the case for larger output areas, but we'd need more granular population data to do better than this.
 
- Actual coverage area of a sensor, as in distance over which air quality measurement is relevant, is more like 50 metres (coverage concept 2 vs. concept 1).

- Coverage distance is not a constant - depends on road canyons, wind direction etc. The Boubrima paper (sees references) uses an approach that considers coverage only to extend along the road (not jump into neighbouring roads), and also factors in wind direction.

- If coverage is changed to be a smaller area (smaller theta) to reflect the distance sensor measurements are accurate over, we should add additional constraints/objectives for preferring sensors to be placed in all parts of the city (if this is indeed desirable).

- Compromise solutions: Is placing a sensor halfway between two point of interest any good for either of them?

- Large theta values lead to higher coverage values in the final network. So a policy maker may just input a large theta value and claim high coverage. Maybe we need a better word than "coverage"?

# Objectives and Weightings

The overall objective is to maximise coverage of the points of interest with a given number of sensors. In other words, to maximise the sum of the coverage across all points of interest.

The tricky bit is incorporating that some areas are better candidates than others (e.g. a sensor in the city centre will cover more people than one on the outskirts of the city), and that we are planning to incorporate several different concepts. The different concepts we wish to include are:

- Coverage of the population as a whole:
   - _**Place of residence**_, **_place of work_**, etc.
- Coverage of high emission areas.
   - Traffic intersections etc.
- Coverage of vulnerable people.
   - **_Young & elderly_**, schools, hospitals etc.

Within each concept there are several different datasets or terms that may contribute, and bold italics above indicate inputs that are currently available in our optimisation.

Each term has to be weighed separately and this is non-trivial - for example is it more important to have a sensor near a school with 500 pupils, a hospital with 500 beds, or at an intersection with 500 queued cars? This is largely determined by the interests of the person/stakeholders generating the network. So they can be variable parameters in the optimisation inputs to some extent, but converting those preferences into sensible values is challenging in itself. There are also different approachea for how those weights can be combined.

## Single Objective

With a single objective, i.e. optimising for a single sub-concept, the weightings are more straightforward to determine. For example, our first optimisations incorporated only total residential population in each output area. The optimisation weight for each output area was then just its population, with the objective to maximise being this weighted sum:
```
total_coverage = sum (OA_population * OA_coverage) / sum(OA_population)
```
Dividing by `sum(OA_population)` gives a resulting `total_coverage` value that lies between 0 (no coverage) and 1 (full coverage).


## Multiple Objectives

### One Optimisation with Combined Weights (current approach)

- One multi-objective optimisation. Each objective has a weighting and we create a single network optimised for those weightings.
  - Pros: Only need to run one optimisation. Will find good compromise locations, e.g. likely to pick locations that are 2nd best for each individual objective.
  - Cons: Maybe less intuitive for decision support tool. Effect of weightings less clear.

### Several Single-Objective Optimisations (Cambridge paper approach)

- Separate optimisation for each objective. Weight each objective by assigning a different number of sensors to each one (the approach in the Cambridge paper)
  - Pros: Nice way to compare good locations for each objective.
  - Cons: Need to run a separate (simpler) optimisation for each objective. May miss compromise locations, e.g. prefer picking a location ranked 1st for one objective than one ranked 2nd for many objectives.

### Multi-Objective Optimisation
- Pareto Front

# Constraints

Number of sensors


### Equality

- Rather than (or as well as) having a preference for sensors to be evenly distributed throughout the city, we may want to have terms to force an even coverage of demographics, e.g. similar number of sensors for each IMD decile.



# Algorithm

## Current Approach: Greedy

- Currently a "homemade" greedy algorithm. Place sensors one by one in whichever location leads to maximum total coverage.

```
For each sensor to be placed:
    For each output area:
        Place sensor at output area centroid.
        Calculate total coverage.
        Save network if it is the best so far.
```

## Alternatives

The exact choice of algorithm is less important (and generally easier to change) than getting the inputs, weights and constraints right, in my opinion. So after having success with a greedy approach as an initial baseline I have not yet invested much time in exploring alternatives. However, genetic algorithms in particular seem to have interesting properties, and are what I would choose to try next.

### Genetic Algorithms

### Exact Solvers 

### Others

- Simulated annealing
- "Standard" Optimisation Solvers


# Considerations for User Interface

### Complexity

- How to present weights in an intuitive way to the user in the frontend?


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

* MIP

# References

- **The "Cambridge paper"**
  - _"Optimal Citizen-Centric Sensor Placement for Air Quality Monitoring: A Case Study of City of Cambridge, the United Kingdom"_, CHENXI SUN, VICTOR O. K. LI et al., 2019, IEEE Access.

- **Boubrima**
  - _"On the Deployment of Wireless Sensor Networks for Air Quality Mapping: Optimization Models and Algorithms"_, Ahmed Boubrima, Walid Bechkit, Hervé Rivano, 2019, HAL