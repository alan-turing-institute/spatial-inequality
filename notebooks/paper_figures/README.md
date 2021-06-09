## Demographic Variables

- **demographics_density.png** Distribution of each variable, all on the same scale using a density
calculated as % of people in the OA, divided by the area of the OA.

- demographics_importance.png: Distribution of each variable, all on the same scale using "importance",
which is the overall coverage provided by placing a sensor in this output area (using theta = 500 m)


## Single Objective (Greedy Algorithm)

- **coverage_vs_nsensors.png** Coverage vs. number of sensors for each objective, up to 55 sensors.

Networks for each objective with theta = 100m or 500m, and nsensors = 10 or 55:

- **pop_children_theta100_500_nsensors10_55.png**
- **pop_elderly_theta100_500_nsensors10_55.png**
- **pop_total_theta100_500_nsensors10_55.png**
- **workplace_theta100_500_nsensors10_55.png**

Bear in mind that we have no data at a granularity smaller than output areas, so with theta = 100 m we're not really calculating coverage within 100 m. It's more like saying that a sensor covers the OA it's in but none of the surrounding OAs benefit from it. Also note that  whatever the value of theta we always consider an OA to be 100% covered if it has a sensor.

Other combinations of theta and no. sensors:

- pop_children_theta100_500_nsensors10_50.png
- pop_children_theta100_500_nsensors10_60.png
- pop_children_theta250_500_nsensors20_60.png
- pop_elderly_theta100_500_nsensors10_50.png
- pop_elderly_theta100_500_nsensors10_60.png
- pop_elderly_theta250_500_nsensors20_60.png
- pop_total_theta100_500_nsensors10_50.png
- pop_total_theta100_500_nsensors10_60.png
- pop_total_theta250_500_nsensors20_60.png
- workplace_theta100_500_nsensors10_50.png
- workplace_theta100_500_nsensors10_60.png
- workplace_theta250_500_nsensors20_60.png


## Comparisons to Urban Observatory (UO)

- urb_obs_sensors_theta_500_nsensors_146.png: Location of UO sensors only (with no coverage map shown)

Two approaches here for calculating coverage of the UO network:

- "Grid coverage": Create a 100 m square grid. Each grid square gets coverage based on the distance to the nearest
sensor. All 146 sensors in the UO network included. I tend to prefer the results of this approach
personally.
  - **urb_obs_coverage_grid_theta_500_nsensors_146.png** Coverage of the UO network
  - **urb_obs_coverage_difference_grid_theta_500_nsensors_55.png** Difference between UO network and our single
  objective networks. Red areas have less coverage in the UO network, blue areas more coverage. We could claim blue areas have an excess of coverage and red areas a deficit of coverage, assuming you were only interestted in creating
  a network optimised for a single objective.

- "OA coverage": Snap all  the urban observatory sensors to the centroid of the OA they are in. This results in 55
OAs with sensors. Then calculate coverage in the same way as our optimisation - if an OA has a sensor it is 100%
covered, if not coverage based on distance to nearest OA with sensor. 2 figure below as above but with the alternative coverage calculation:
  - urb_obs_coverage_oa_theta_500_nsensors_55.png
  - urb_obs_coverage_difference_oa_theta_500_nsensors_55.png

Also one comparing the UO network against our multi-objective networks:

- **multiobj_theta500_55sensors_above_urbobs.png** Coverage of 200 different 55 sensor networks shown for
each of the objectives (so each network has a corresponding marker somewhere within each of the 4 clusters of points). Horizontal line shows the coverage of the UO network for each objective (using the "OA coverage" approach). Networks coloured blue have better coverage than the UO network across all 4 objectives.
Networks coloured pink have worse workplace coverage than the UO network (but _all_ networks have better coverage
than the UO network for the other 3 objectives). But you can see that to get workplace coverage that matches the
UO network you must sacrifice some coverage of the other 3, for example (i.e. there's a pink band across the top  
of the other 3).

Main criticisms here are probably a) that we don't include traffic/other data around where air quality is likely
to be poor, b) we only consider data at OA-level, c) we don't consider practicalities of where sensors can be
(safely) installed. However, there are parts of the city that have a deficit for all objectives, e.g. south west and north east areas.

## 2 Objectives (Genetic Algorithm): Workplace and Elderly

I have focused mostly on optimising for all 4 objectives, but also made a few figures with workplace and elderly
only (the two most different sets of populations):

Workplace coverage vs. elderly coverage:

- **2obj_theta500_55sensors.png**
- 2obj_theta500_10sensors.png

Set of 4 networks varying from maximal elderly coverage  (top left) to maximal workplace coverage (bottom right) -
note sensors move to city centre as you move from top left to bottom right, and you gain a large increase in
workplace coverage without a huge amount in coverage of the elderly:

- **2obj_spectrum_theta500_55sensors.png**


## 4 Objectives (Genetic Algorithm)

- 200 networks displayed in the same way as `multiobj_theta500_55sensors_above_urbobs.png` above:
  - multiobj_theta100_55sensors_above10cov.png: For theta=100m, networks coloured blue have at least 10% coverage
  of all 4 objectives.
  - **multiobj_theta500_55sensors_above45cov.png**: For theta=500m, networks coloured blue have at least 45% coverage of
  all 4 objectives. 62 out of 200 networks meet this criteria.
  - multiobj_theta500_55sensors_workabove65cov.png: For theta=500m, networks coloured blue have at least 65% coverage of workplace (picked partly to give an example of networks that have better workplace coverage than the UO network but also better coverage of the other 3 objectives)
  - `multiobj_highlightsingle` folder: For theta=500m, highlight each individual network separately (one figure for each network)


- "Compromise" networks: Maximise the minimum coverage across all the objectives. Tends to favour coverage of elderly
(since they're hardest to cover)
  - multiobj_compromise_theta100_55sensors_cov0.117.png: theta=100m, all objectives have coverage > 0.117
  - multiobj_compromise_theta500_55sensors_cov0.48.png: theta=500m, all objectives have coverage > 0.48

- Network with the maximal possible coverage of children that also has workplace coverage > 0.65
  - **multiobj_wplace0.65_child0.47_theta500_55sensors.png**
