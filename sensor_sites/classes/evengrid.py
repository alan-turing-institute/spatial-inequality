#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Even-spacing grid point set generation class
Generates an evenly spaced set of points within a group of LADs

Created on Created on Thur Jan 16 2020 09:30

@author: ndh114
"""

import math

import geopandas as gpd
import numpy
import pandas as pd

from .config import Config
from .pointset import PointSet


class EvenGrid(PointSet):
    def __init__(self, npoints=100, lad_codes=None):
        super(EvenGrid, self).__init__(
            npoints, lad_codes, "Even-spacing grid generator"
        )

    def generate(self):
        super().generate()
        snapped = None
        if self.aoi is not None:
            # Safe to proceed
            snapped = self.snap_to_roads(self.even_spaced_points_in_area())
        else:
            # Some kind of error, reported lower down
            self.logger.error("Point generation exiting with error status")
        return snapped

    def even_spaced_points_in_area(self):
        """
        | Generate even-spaced points in the AOI (assumed supplied as a single polygon
        in BNG)
        """
        self.logger.info("Generate evenly-spaced points within selected LADs")

        # Get total area of AOI
        aoi_area = self.aoi.geometry[0].area

        # Get area of AOI bounding box, with a small buffer
        buff = 100
        minx, miny, maxx, maxy = self.aoi.total_bounds + [-buff, -buff, buff, buff]
        aoi_bbox_area = (maxx - minx) * (maxy - miny)

        # Revise the number of points to generate such that there will be 'npoints' in
        # the polygon
        tot_npoints = math.ceil(self.npoints * aoi_bbox_area / aoi_area)

        xlist = []
        ylist = []
        npoints_per_side = math.ceil(math.sqrt(tot_npoints))
        for x in numpy.linspace(minx + buff, maxx - buff, npoints_per_side):
            for y in numpy.linspace(miny + buff, maxy - buff, npoints_per_side):
                xlist.append(x)
                ylist.append(y)
        points_df = pd.DataFrame({"x": xlist, "y": ylist})
        points_gdf = gpd.GeoDataFrame(
            points_df,
            crs={"init": Config.get("BRITISH_NATIONAL_GRID")},
            geometry=gpd.points_from_xy(points_df.x, points_df.y),
        ).sample(self.npoints)

        self.logger.info("Even-spaced point generation complete")

        return points_gdf
