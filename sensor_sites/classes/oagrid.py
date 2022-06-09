#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OA centroid point set generation class
Generates a set of points at the centroid of each OA within a group of LADs
Randomly selects 'npoints' of these if there are more than the number asked for

Created on Created on Thur Jan 16 2020 11:03

@author: ndh114
"""

import geopandas as gpd
import psycopg2

from .config import Config
from .pointset import PointSet


class OaGrid(PointSet):

    __OA_DBASE = "nismod-boundaries"
    __OA_TABLE = "oas_2011_uk_with_lad_gor_2016"

    def __init__(self, npoints=100, lad_codes=None):
        super(OaGrid, self).__init__(npoints, lad_codes, "OA centroid grid generator")

    def generate(self):
        super().generate()
        snapped = None
        if self.aoi is not None:
            # Safe to proceed
            snapped = self.snap_to_roads(self.oa_centroids())
        else:
            # Some kind of error, reported lower down
            self.logger.error("Point generation exiting with error status")
        return snapped

    def oa_centroids(self):
        """
        | Generate points at OA centroids within the supplied LADs
        """
        self.logger.info("Generate points at centroids of all OAs in selected LADs")

        con = None
        points_gdf = None
        try:
            con = psycopg2.connect(
                database=OaGrid.__OA_DBASE,
                user=Config.get("NISMOD_DB_USERNAME"),
                password=Config.get("NISMOD_DB_PASSWORD"),
                host=Config.get("NISMOD_DB_HOST"),
            )
            sql = (
                "SELECT oa_code, lad_code, centroid as geometry FROM {} "
                "WHERE lad_code IN ({})"
            ).format(
                OaGrid.__OA_TABLE,
                ",".join(list(map(lambda elt: "'{}'".format(elt), self.lad_codes))),
            )
            points_gdf = gpd.GeoDataFrame.from_postgis(
                sql, con, geom_col="geometry"
            ).sample(self.npoints)
        except psycopg2.Error as pgerr:
            self.logger.error(
                (
                    "Failed to retrieve OA centroids from NISMOD database " "- error {}"
                ).format(pgerr)
            )
        finally:
            if con is not None:
                con.close()

        self.logger.info("OA centroid point generation complete")

        return points_gdf
