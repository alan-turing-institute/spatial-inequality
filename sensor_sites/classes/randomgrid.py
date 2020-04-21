#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random point set generation class
Generates a random set of points within a group of LADs

Created on Created on Tue Jan 14 2020 17:08

@author: ndh114
"""

import random

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from .config import Config
from .pointset import PointSet


class RandomGrid(PointSet):
    def __init__(self, npoints=100, lad_codes=None):
        super(RandomGrid, self).__init__(npoints, lad_codes, "Random grid generator")

    def generate(self):
        super().generate()
        snapped = None
        if self.aoi is not None:
            # Safe to proceed
            snapped = self.snap_to_roads(self.random_points_in_area())
        else:
            # Some kind of error, reported lower down
            self.logger.error("Point generation exiting with error status")
        return snapped

    def random_points_in_area(self):
        """
        | Generate random points in the AOI (assumed supplied as a single polygon in BNG)
        """
        self.logger.info("Generate random points within selected LADs")

        # Step 1: create a GeoDataFrame containing npoints random points within the AOI
        xlist = []
        ylist = []
        minx, miny, maxx, maxy = self.aoi.total_bounds
        aoi_polygon = self.aoi.geometry[0]
        n_generated = 0
        while n_generated < self.npoints:
            # Generate a random point within the box of the AOI polygon
            gen_x = random.uniform(minx, maxx)
            gen_y = random.uniform(miny, maxy)
            pt = Point(gen_x, gen_y)
            # Check the generated point in fact lies in the AOI, if not generate another
            if aoi_polygon.contains(pt):
                xlist.append(gen_x)
                ylist.append(gen_y)
                n_generated += 1
        points_df = pd.DataFrame({"x": xlist, "y": ylist})
        points_gdf = gpd.GeoDataFrame(
            points_df,
            crs={"init": Config.get("BRITISH_NATIONAL_GRID")},
            geometry=gpd.points_from_xy(points_df.x, points_df.y),
        )

        self.logger.info("Random point generation complete")

        return points_gdf
