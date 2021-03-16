
# Optimisation

To define and run an optimisation for generating a network of sensors we need:
- A set of possible sensor locations.
- A concept of coverage - to what extent do the areas neighbouring a sensor benefit?
- An objective, or a set of objectives, to maximise.
- A set of constraints - conditions that must be met for a solution to be viable.
- An algorithm to pick the best sensor locations to maximise the objective.

In words, the optimisation problem to solve is roughly: _"Choose sensor locations to maximise the coverage of our objectives, subject to the network meeting the defined constraints"_.

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

The tricky bit is incorporating that some areas are better candidates than others (e.g. a sensor in the city centre will cover more people than one on the outskirts of the city), and that we are planning to incorporate several different concepts. The different concepts we wish to include are (at minimum):

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
Dividing by `sum(OA_population)` gives a resulting `total_coverage` value that lies between 0 (no coverage) and 1 (full coverage). The `OA_coverage` values are determined by the nearest sensor to each output area, as described in the coverage section above. The sums are over output areas.

This can easily be modified for any criteria that can be represented by a single count or rating - for example number of workers in an output area, number of students at a school, number of cars at an intersection per day, or similar, by replacing the `OA_population` terms above with the relevant metric.

The optimisation chooses sensor locations that maximise the total coverage, as defined above.


## Multiple Objectives

As soon as a second concept/objective is added to the optimisation it becomes more difficult to define what the appropriate weight is for each location. I have come across three main alternatives:

### One Optimisation with Combined Weights (current approach)

The single objective equation above can be rewritten in a more general form as:
```
total_coverage = sum(OA_weight * OA_coverage) / sum(OA_weight)
```
This is written as considering output area stats only, but could easily represent other types of location as well. The weight `OA_weight` in this case is not a number representing a single concept but an overall value combining several concepts. For example, we could consider a weighted combination of residential population and place of work by doing:
```
OA_weight =
[(pop_importance * pop_weight) + (worker_importance * worker_weight)] /
(pop_importance + worker_importance)

pop_weight = OA_population / sum(OA_population)

worker_weight = OA_workers / sum(OA_workers)
```
The `pop_weight` term is the same as the single objective weight above, and normalised by the total population so that the sum of the population weights equals one. `worker_weight` is the same but for the number of workers in the output area. In the overal weight (`OA_weight`) these are added together with additional weighting terms `pop_importance` and `worker_importance`, which determine whether stronger preference will be given to coverage of residential population or coverage of workers (plus another normalisation so that the `OA_weights` sum to one).

This is available in the current optimisation code (and the API) as well as a further option to add a different weight for each age of residents. The age weighting works as follows. Say an output area has 50 children, 200 adults, and 50 elderly people. We can define a weighting factor of 3 for children, 1 for adults, and 2 for the elderly (or any value we choose). In this case the the optimisation treats the OA population as effectively being 150 children (50 x 3), 200 adults (200 x 1), and 100 elderly (50 x 2). Note that in this example, despite the higher weighting for children and the elderly, the adult population still is the biggest contributor to the overall weight for the OA. It could be framed differently to apply the weightings at a group level as opposed to an individual count level - i.e. we treat coverage of children as a separate objective, and weight the children objective 3 times more than the adult objective.

**Advantages of this approach:**
- Once the weighting factors have been calculated, only one single-objective optimisation needs to be run to get the final network.
- Capable of finding good compromise locations, e.g. an OA ranked 2nd for number of children and elderly.

**Disadvantages of this approach:**
- Difficult to pick, or normalise, the weights in a way that gives meaningful compromise/comparison between the different objectives. E.g. how to compare 100 pupils in a school to 100 residents in a care home.
- Also difficult to translate the weights used in the backend into intuitive rating/value ranges in the decision support tool.

### Several Single-Objective Optimisations (Cambridge paper approach)

In the Cambridge paper, instead of attempting to run a multiple-objective optimisation they instead run many single-objective optimisations. Specifically, they do one optimisation for population coverage, one for coverage of vulnerable people (schools and hospitals), and one for coverage of traffic intersections.

In this approach the weighting for each objective is determined by assigning a different number of sensors to each optimisation objective - for example a 15-sensor optimisation for traffic coverage, a 10-sensor optimisation for coverage of the vulnerable, and a 5-sensor optimisation for population coverage. The final network is the 30-sensor network resulting by combining the results of the three optimisations.

In some cases a sensor may be placed in the same (or similar) location in more than one of the optimisations. If this happens the two sensors can be merged into one in the final solution, and an additional sensor can be placed elsewhere (in the best location to increase coverage in one of the objectives).

**Advantages of this approach:**
- Simplifies the process of weighting the objectives, or at least gives a more intuitive way to state preferences.
- Each individual optimisation can be relatively simple, and each one could use a completely different algorithm or formulation.
- If using a greedy optimisation the decision about how many sensors to assign to each objective can be made afterwards,  i.e. run an initial optimisation to rank the top sites for each objective then compare different combinations (top 10 for objective 1 and top 5 for objective 2, vs. top 5 for objective 1 and top 10 for objective 2 etc.)

**Disadvantages of this approach:**
- Requires running a separate optimisation for each objective, so will take around n_objectives times longer than the combined weights approach if using a single thread. However, it should be trivial to run them in parallel.
- As each optimisation only considers a single objective compromise locations may be missed, e.g. less likely to select sites that are good for all objectives but not best for any.


### Multi-Objective Optimisation

Some algorithms, for example some implementations of genetic algorithms, are able to run a single optimisation containing multiple objectives without having to state explicit preferences between them initially. When approached this way the optimisation output (in my understanding) is not usually a single solution but a set (or "population") of viable candidate solutions, which ideally are all distinct from each other.

Each solution in the population should lie on the "Pareto front" (if the optimisation was successful and converged fully). A solution is on the Pareto front if it is impossible to change (i.e. it is impossible to move a sensor) without making at least one of the objectives worse. In other words, solutions (sensor networks) on the Pareto front are optimal results for some combination of the objectives.

This means the population of solutions should contain a spectrum of results ranging from a sensor network optimised only for total population coverage, to one optimised only for coverage of vulnerable population, as well as different combinations of the two, for example. This approach is discussed in the Jankowski paper.

After running the optimisation the user will have to go through a process to decide which of the solutions in the population suits them best. There may be visualisation and algorithmic techniques to help with this, some of which are also mentioned or referenced in the Jankowski paper.

**Advantages of this approach:**
- Generates full spectrum of possible solutions, including solutions that strongly prefer a single objective and compromise solutions considering many objectives. Approaches above only generate one of these, not both.
- Comparing/contrasting different solutions seems like something that could work well in the decision support tool. Also the option that the decision support tool presents a previously calculated population of possible solutions, rather than triggering new optimisation runs in the backend.
- Only need to run one optimisation.

**Disadvantages of this approach:**
- Limits choice of optimisation algorithm to more complex, probably slower, options.
- May be left with many (e.g. hundreds) of possible networks to decide between.


# Constraints

Constraints are conditions that must be met for a solution to be viable. Solutions that do not meet the constraints are not allowed.

Currently we have only one constraint - the number of sensors in the network. In principle this could be changed to be a total budget for sensors that gets split different sensor types, though this would add a reasonable amount of complexity to the formulation of the optimisation without much reward (in my opinion).

We could maybe consider adding equality conditions as constraints as well, to remove networks that don't cover certain IMD deciles, or ones that are strongly biased to a certain part of the city. However, I think these should be added as objectives rather than constraints (and I'm not sure they should be part of the optimisation in the first place).


# Algorithm

The exact choice of algorithm is less important (and generally easier to change) than getting the inputs, weights and constraints right, in my opinion. So after having success with a greedy approach as an initial baseline I have not yet invested much time in exploring alternatives. However, genetic algorithms in particular seem to have interesting properties for multi-objective optimisation (discussed above), and are what I would choose to try next.

## Current Approach: Greedy

This is also the approach taken in the Cambridge paper. As they are simple conceptually and simple to implement, we currently use a "homemade" greedy algorithm.

Sensors are placed one at a time at whichever location leads to maximum total coverage. In other words, we try placing a sensor at all the available locations and leave it at whichever location gave the best total coverage. That sensor's position is fixed for the rest of the optimisation. The process is repeated until a network with the requested number of sensors has been generated.

Greedy algorithms are unlikely to converge to the global optimum, but quickly give reasonable results and were a natural choice for the first baseline. The Cambridge paper includes proofs that greedy algorithms are within some factor of the global optimum, given some conditions.


## Genetic Algorithms

My rough understanding of genetic algorithms is they work using the following process:

1. Initialise a population of different sensor networks.
2. Evaluate the coverage objectives for each network.
3. Selection: Select some fraction of the best performing networks.
4. Crossover: Merge the results of networks to create "child" networks that share properties with both their parents.
5. Mutation: Make some random changes to the solutions.
6. Repeat steps 2 to 5 until a termination condition is met.

Difficulties in getting them to work well seem to be related to the choice of crossover and mutation functions, particularly in a spatial context. This is discussed in the Tong paper.

Genetic algorithms are what I plan to investigate next. 

## Exact Solvers

Exact solvers give some guarantee of finding the global optimum solution rather than good close-to-optimal solutions like the other approaches here. However, the size/complexity of problem that can be solved with exact solvers are more limited and the solvers are normally commercial software.

Gurobi seems to be popular.

## Others

There are many other optimisation approaches, including:
- Bees and ant colony algorithms
- Simulated annealing
- Mixed integer programming
- "Standard" Optimisation Solvers

The optimisation libraries mentioned below generally include many algorithms of different types so different approaches could be tried hopefully without too much difficulty.

# Considerations for User Interface

### Complexity

- How to present weights in an intuitive way to the user in the frontend?


### Speed

- A typical user of the decision support tool may not be willing to wait more than a few minutes for a result.
  - Who is the typical user? Member of public may only wait minutes, policy maker may be willing to wait a day.
- Adding complexity adds computation time - definitely feasible that it could take closer to hours than minutes. What can we provide within a few seconds?


# Libraries

The two main libraries I have or plan to invest time in are:

* PyGMO
   - European Space Agency developed optimisation library (original source is Pagmo, a C++ library).
   - Has a wide selection of algorithms of different types each with a common interface.
   - This is the first package I started playing with, with some examples in `notebooks/population_optimisation.ipynb`. I got it running but had problems with either too many sensors being generated or sensors being placed outside the local authority boundary. Like any library, will need some time understanding the specifics of each algorithm and how they should be implemented to get it working properly.
   - Links: https://github.com/esa/pygmo2, https://esa.github.io/pygmo2

* pymoo
  - Looks to be quite new but has implementations of the NSGA algorithm mentioned in the Jankowski paper and clear examples of calculating the Pareto front in its documentation.
  - Links: https://pymoo.org/, https://github.com/msu-coinlab/pymoo


Others I'm aware of include:

* scipy: https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html ("standard" optimisation algorithms - good for quick/simple implementations)

* PyTorch: https://pytorch.org/docs/stable/optim.html
  
* MIP: https://python-mip.com/ (mixed integer programming)

# References

- **The "Cambridge paper"**
  - _["Optimal Citizen-Centric Sensor Placement for Air Quality Monitoring: A Case Study of City of Cambridge, the United Kingdom"_, CHENXI SUN, VICTOR O. K. LI et al., 2019, IEEE Access.](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=8681135)

- **Boubrima**
  - _["On the Deployment of Wireless Sensor Networks for Air Quality Mapping: Optimization Models and Algorithms"_, Ahmed Boubrima, Walid Bechkit, Hervé Rivano, 2019, HAL](https://hal.inria.fr/hal-02157476/document)

- **Jankowski**
  - _["An exploratory approach to spatial decision support"_, Piotr Jankowski, Grant Fraley & Edzer Pebesma, 2014, Computers, Environment and Urban Systems 45](https://www.sciencedirect.com/science/article/pii/S0198971514000246?via%3Dihub)

- **Tong**
  - [_"Heuristics in Spatial Analysis: A Genetic Algorithm for Coverage Maximization"_, Daoqin Tong , Alan Murray & Ningchuan Xiao, 2009, Annals of the Association of American Geographers](https://www.tandfonline.com/doi/abs/10.1080/00045600903120594?journalCode=raag20)
