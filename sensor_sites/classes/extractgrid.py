#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract from existing data point set generation class
Generates a sample set of 'npoints' points from an existing dataset 

Created on Created on Thur Jan 16 2020 11:03

@author: ndh114
"""

from os import R_OK, access
from os.path import isfile

import geopandas as gpd

from .pointset import PointSet


class ExtractGrid(PointSet):
    def __init__(self, npoints=100, lad_codes=None, datafile_path=None):
        super(ExtractGrid, self).__init__(
            npoints, lad_codes, "Extract from existing dataset point generator"
        )
        if not isfile(datafile_path) or not access(datafile_path, R_OK):
            raise ValueError("{} is not a readable file".format(datafile_path))
        else:
            self.dataset = gpd.read_file(datafile_path)

    def generate(self):
        points_gdf = None
        if self.dataset is not None:
            points_gdf = self.dataset.sample(self.npoints)
        else:
            self.logger.error("Point generation failed due to invalid input dataset")
        return points_gdf
