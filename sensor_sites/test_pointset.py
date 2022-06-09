#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test bed for point set generation functionality
Created on Mon Jan 10 14:58 2020

@author: ndh114
"""
import logging
import unittest
from os import path, remove

import geopandas as gpd
from classes import Config, EvenGrid, ExtractGrid, OaGrid, RandomGrid


class TestPointSet(unittest.TestCase):
    def absolute_file_output_path(self, relpath):
        return "{}/unit_test_outputs/{}".format(Config.get("DATA_DIRECTORY"), relpath)

    def read_geopackage(self, gpkg_path):
        return gpd.read_file("{}/{}".format(Config.get("DATA_DIRECTORY"), gpkg_path))

    def write_geopackage(self, gdf, gpkg_path):
        file_path = self.absolute_file_output_path(gpkg_path)
        if path.exists(file_path):
            remove(file_path)
        gdf.to_file(file_path, driver="GPKG")

    def setUp(self):
        logging.basicConfig(
            level=Config.get("LOG_LEVEL"),
            format=Config.get("LOG_FORMAT"),
            datefmt=Config.get("LOG_DATE_FORMAT"),
            filename=Config.get("LOG_FILE"),
            filemode="w",
        )
        self.logger = logging.getLogger("TestPointSet")

    def test_pointset_oa(self):
        """
        Generate a point set with points at centroids of all OAs
        """
        set_size = 400
        out_file = "oa_centroid_points.gpkg"
        out_path = self.absolute_file_output_path(out_file)
        out_gdf = OaGrid(set_size, ["E08000021"]).generate()
        self.assertTrue(len(out_gdf) == set_size)
        self.write_geopackage(out_gdf, out_file)
        self.assertTrue(path.exists(out_path) and path.getsize(out_path) > 0)

    def test_pointset_grid(self):
        """
        Generate a point set with points on a regular grid
        """
        set_size = 250
        out_file = "even_spaced_points.gpkg"
        out_path = self.absolute_file_output_path(out_file)
        out_gdf = EvenGrid(set_size, ["E08000021"]).generate()
        self.assertTrue(len(out_gdf) == set_size)
        self.write_geopackage(out_gdf, out_file)
        self.assertTrue(path.exists(out_path) and path.getsize(out_path) > 0)

    def test_pointset_extract(self):
        """
        Generate a point set with points extracted from an existing dataset
        """
        set_size = 500
        out_file = "extracted_points.gpkg"
        out_path = self.absolute_file_output_path(out_file)
        out_gdf = ExtractGrid(
            set_size,
            ["E08000021"],
            "{}/newcastle_lamp_posts.gpkg".format(Config.get("DATA_DIRECTORY")),
        ).generate()
        self.assertTrue(len(out_gdf) == set_size)
        self.write_geopackage(out_gdf, out_file)
        self.assertTrue(path.exists(out_path) and path.getsize(out_path) > 0)

    def test_pointset_random(self):
        """
        Generate a point set with points generated randomly within a polygon
        """
        set_size = 350
        out_file = "random_points.gpkg"
        out_path = self.absolute_file_output_path(out_file)
        out_gdf = RandomGrid(set_size, ["E08000021"]).generate()
        self.assertTrue(len(out_gdf) == set_size)
        self.write_geopackage(out_gdf, out_file)
        self.assertTrue(path.exists(out_path) and path.getsize(out_path) > 0)


if __name__ == "__main__":
    unittest.main()
