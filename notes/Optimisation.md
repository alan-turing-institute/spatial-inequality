
# Optimisation



# Coverage

Each sensor that is placed gives "coverage" of a certain area. In my opinion, there are three different coverage concepts, each with different merits. These are:

1) Distance over which a sensor is expected to give an accurate measurement (i.e. how far away can I stand from a sensor and still be confident that the quality of air I'm breathing in is similar to the sensor's measurement?) This distance seems to be tens of metres (maybe 30-50 metres).

2) Whether a region/part of the city contains a sensor. This is relevant for questions such as whether a network gives a representative sample of all the different environments in the city, and whether members of the public feel as though the local government is taking sufficient interest in their area. The distance scale here is maybe the size of a neighbourhood, or hundreds of metres.

3) Required density or distribution of sensors to be able to create an accurate air quality model for the whole city, i.e. whether placing a sensor in a given location will lead to a significant improvement in a model's predictions (potentially for the whole city).

Concept 3 is particularly relevant for air quality modelling, whereas Concept 2 is perhaps more relevant for social or political policy decisions. Concept 1 has relevance for both, but in particular prioritises coverage of individuals (or small areas) as opposed to coverage of (larger) areas.

## Current Approach

The coverage concept we've used so far is most like concept 2 above. This is motivated by factors such as:

- We'd like our work to be applicable to cities without a pre-existing sensor network or air quality model.
- There will be a relatively small number of sensors (compared to the size of the population/the size of the city).
- The focus of the project isn't air quality modelling and developing a model for Newcastle would be a significant time investment (even if building on previous work).
- The focus of the project _is_ coverage of population, or coverage of under-represented demographics.

Our "coverage" metric is inspired by the population "satisfaction" metric in the Cambridge paper. They claim (or approximate) that the level of satisfaction a member of the public has with a given sensor network is dependent only on the distance between their place of residence and the nearest sensor.

They use an exponential decay (justified for its mathematical properties rather than any claim on how distance determines actual satisfaction, I think), defined as:

$C = \exp(-d/\theta)$

Where $C$ is the coverage at a point, $d$ is the distance between that point and the nearest sensor, and $\theta$ is a decay rate parameter (large $\theta$ values mean coverage extends over a larger distance). Coverage equals 1 (or 100%) if a sensor is placed at the point of interest, or 1/e (0.37) if the nearest sensor is $\theta$ metres away.

The Cambridge paper uses a value of $\theta = 1000$ metres (I believe), which is the size of grids in the population data they use (they don't justify this value beyond that). We have used a default value of $\theta = 500$ metres so far, which makes the coverage as a function of distance look like this:
![](figs/coverage.png)

Large theta values (I would consider 500 metres to be large) lead to a preference for networks with sensors evenly distributed around the whole city. Small theta values (say 100 metres) lead to a preference for sensors to be placed in areas of high density/interest, even if they are all clustered in the same part of the city.

## Challenges/Issues

- So far we have considered only output area stats and sensors placed at output area centroids. If an output area has a sensor at its centroid we consider the whole output area to be 100% covered. This is clearly not the case for larger output areas, but we'd need more granular population data to do better than this.
 
- Actual coverage area of a sensor, as in distance over which air quality measurement is relevant, is more like 50 metres (coverage concept 2 vs. concept 1).

- Coverage distance is not a constant - depends on road canyons, wind direction etc. The Boubrima paper (sees references) uses an approach that considers coverage only to extend along the road (not jump into neighbouring roads), and also factors in wind direction.

- If coverage is changed to be a smaller area (smaller theta) to reflect the distance sensor measurements are accurate over, we should add additional constraints/objectives for preferring sensors to be placed in all parts of the city (if this is indeed desirable).

- Compromise solutions: Is placing a sensor halfway between two point of interest any good for either of them?

- Large theta values lead to higher coverage values in the final network. So a policy maker may just input a large theta value and claim high coverage. Maybe we need a better word than "coverage"?

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

# References

- **The "Cambridge paper"**
  - _"Optimal Citizen-Centric Sensor Placement for Air Quality Monitoring: A Case Study of City of Cambridge, the United Kingdom"_, CHENXI SUN, VICTOR O. K. LI et al., 2019, IEEE Access.

- **Boubrima**
  - _"On the Deployment of Wireless Sensor Networks for Air Quality Mapping: Optimization Models and Algorithms"_, Ahmed Boubrima, Walid Bechkit, Hervé Rivano, 2019, HAL