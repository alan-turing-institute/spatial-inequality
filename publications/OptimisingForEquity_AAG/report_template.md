# {{la_name}} ({{la_code}})

## Distribution of Demographic Variables

### Density

Density of each variable, expressed as the percentage of people from that demographic in an output area divided by the area of the output area.

![]({{fig_density}})

### Importance

Total coverage of the local authority provided by placing a single sensor in any output area.

![]({{fig_importance}})

## Single-Objective Networks

Networks optimised for the coverage of one objectively only (for example, maximal coverage of children without taking into account the coverage of older residents of the working population). Generated with a greedy algorithm. Networks with different numbers of sensors (N) and different coverage distances ($\theta$) are shown. Larger values of the coverage distance prioritise networks with equitable coverage of the local authority as a whole, smaller values prioritise local coverage, for example placing sensors in areas of high population density (even if that means placing many sensors close together).

### Coverage vs. No. Sensors

How the total coverage of each demographic's population increases when adding more sensors to a network.

![]({{fig_coverage_vs_nsensors}})

### {{total_pop_name}}

![]({{fig_totalpop}})

### {{children_name}}

![]({{fig_children}})

### {{older_name}}

![]({{fig_older}})

### {{work_name}}

![]({{fig_workers}})

## Comparison with Urban Observatory

How networks generated with our single-objective greedy algorithm compare to the pre-existing Urban Observatory network of sensors.

In the difference figures below, orange regions indicate where our generated networks have higher coverage (Urban Observatory network has a defecit of coverage of that demographic in that area), and purple regions where the Urban Observatory network has higher coverage (Urban Observatory has an excess of coverage in the area for that demographic). Note that, for the comparison, we generate networks with the same number of sensors as the number of different output areas the Urban Observatory network covers (e.g. if the Urban Observatory network has 146 sensors in 55 output areas, we compare it to a network generated with a sensor in 55 output areas using our approach.)

### Urban Observatory Sensor Locations

Point locations of all sensors in the Urban Observatotry network.

![]({{fig_urb_obs_sensors}})

### Urban Observatory Gridded Coverage

Coverage calculated on a 100 metre square grid, including all of the individual Urban Observatory sensor point locations.

![]({{fig_urb_obs_coverage_grid}})

![]({{fig_urb_obs_coverage_diff_grid}})

### Urban Observatory Output Area Coverage

Coverage calculated by moving each Urban Observatory sensor to the population-weighted centroid of the output area it is in. This then let's a direct comparison between the Urban Obserrvatory network and our networks to be made (as our networks place one sensor per output area, each at an output area population-weighted centroid.)

![]({{fig_urb_obs_coverage_oa}})

![]({{fig_urb_obs_coverage_diff_oa}})

## Multi-Objective Networks

Many networks generated to show a range of possible compromise solutions between all the demographic variables (objectives), made using the genetic algorithtm NSGA2.

The swarm plots below show the coverage of each network for each of the objectives (so a network has a point in each of the swarms). Points (networks) highlighted blue meet all the criteria in the section title above the plot, networks coloured pink fail to meet at least one of the criteria for at least one of the objectives.

### All Objectives Above {{all_threshold}}

![]({{fig_all_above_threshold}})

### Coverage of {{work_name}} Above {{work_threshold}}

![]({{fig_work_above_threshold}})

### Max Coverage of {{children_name}} with {{work_name}} Coverage Above {{work_threshold}}

![]({{fig_max_child_work_above_threshold}})

### Coverage Above Urban Observatory

Horizontal lines indicate the coverage of the Urban Observatory network for each of the objectives. Networks coloured blue have better coverage than the Urban Observatory network for all objectives.

![]({{fig_coverage_above_uo}})

### Maximise Minimum Objective Coverage

Maximising the minimum coverage of any objectives tends to prioritise the demographic variable that is most widely spread around the local authority
(rather than being concentrated in the city centre, for example).

![]({{fig_max_min_coverage}})

##  Two Objective Networks ({{obj_1}} and {{obj_2}})

Many networks generated to show a range of possible compromise solutions between two demographic variables (objectives), made using the genetic algorithtm NSGA2. Limiting to two objectives makes it easier to visualise the trade-off between different objectives.

### Coverage of {{obj_1}} vs. {{obj_2}}

How increasing the coverage of one objective impacts the coverage of the second objective.

![]({{fig_obj1_vs_obj2}})

### Spectrum of Networks

Range of 4 networks from maximising the coverage of objective 1 (to the detriment of objective 2), to maximising the coverage of objective 2 (to the detriment of objective 1), with compromises between them in-between. 

![]({{fig_spectrum}})
