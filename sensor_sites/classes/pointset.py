#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point set generation base class

Created on Created on Fri Jan 10 2020 16:20

@author: ndh114
"""

import logging

import geopandas as gpd
import requests
from cerberus import Validator

from .config import Config


class PointSet:

    __ARG_SCHEMA = {
        'npoints': {
            'type': 'integer',
            'required': True,
            'min': 20,
            'max': 5000,
            'nullable': False
        },
        'lad_codes': {
            'type': 'list',
            'required': True,
            'schema': {
                'type': 'string',
                'regex': '^[A-Z][0-9]{8}$'
            }
        },
        'loghandle': {
            'type': 'string',
            'required': False,
            'nullable': True
        }
    }

    def __init__(self, 
                 npoints=100, 
                 lad_codes=None,
                 loghandle=__name__
                 ):
        """
        |  Constructor
        |  
        |  Keyword arguments:
        |  npoints      -- Number of points to generate (default 100)
        |  lad_codes    -- LAD codes specifying the area of interest (AOI)
        |  loghandle    -- Identifier for child class logging
        """

        # Check detailed arguments against Cerberus schema
        args = {
            'npoints': npoints,
            'lad_codes': lad_codes,
            'loghandle': loghandle
        }
        v = Validator()
        args_ok = v.validate(args, self.__ARG_SCHEMA)

        self.logger = logging.getLogger(loghandle)

        if args_ok:

            # Validated arguments against schema ok            
            self.logger.info('Argument validation against schema passed')                                         
            self.logger.info(', '.join('%s: %s' % arg for arg in args.items()))
            self.logger.info('End of argument list') 
            self.npoints     = npoints
            self.lad_codes   = lad_codes

        else:

            # Failed schema validation
            self.logger.warning('Argument validation against schema failed, errors follow:')
            for name, msg in v.errors:
                self.logger.warning('--- {} returned "{}"'.format(name, msg))
            raise ValueError('Schema validation failure')            

        # Computed members
        self.aoi = None

    def generate(self):
        """
        | Method to compute the AOI GeoDataFrame from the LAD codes supplied
        | Note: a 'generate' method should be implemented for each child class, with the first line being:
        | super().generate()
        """
        self.aoi = self.nismod_db_call('boundaries/lads', None, lad_codes=self.lad_codes)

    def snap_to_roads(self, points):
        """
        | Snap a generated point set to the road network within the area of interest
        | Grateful to https://gis.stackexchange.com/questions/306838/snap-points-shapefile-to-line-shapefile-using-shapely
        | as I don't think I would have ever worked out how to do this otherwise!
        |
        | Arguments:
        | points          -- GeoDataFrame containing the points to snap
        |
        | Returns:
        | updated_points  -- New GeoDataFrame containing closest points on the road network to the originals
        """
        # Step 1: get road network lines from NISMOD-DB++ and spatially index (may take some time...)
        # Note: this output should be cached as GeoJSON somewhere eventually to avoid the performance overhead
        roads_gdf = self.nismod_db_call('networks/highways', 'edges', scale='lad', area_codes=self.lad_codes)
        roads_gdf_u = roads_gdf.geometry.unary_union

        # Step 2: interpolate and project generated points onto road network
        points2 = points.copy()
        points2['geometry'] = points2.apply(lambda row: roads_gdf_u.interpolate(roads_gdf_u.project(row.geometry)), axis=1)

        return points2

    def nismod_db_call(self, verb, collection_name='edges', **kwargs):
        """
        |  Make a generic call to NISMOD-DB++ and return a single FeatureCollection as a GeoDataFrame
        |  Arguments:
        |  verb                 -- NISMOD API verb (part of the REST path after /api/data, so may contain '/')
        |  collection_name      -- For multiple FeatureCollections (e.g. road networks), which one to return (e.g. 'nodes'/'edges')
        |  kwargs               -- Arguments corresponding to the above REST verb
        |
        |  Returns:
        |  Single GeoDataFrame extracted from the GeoJSON
        """
        geojson_gdf = None
        api_params = kwargs
        api_url = '{}/{}'.format(Config.get('NISMOD_DB_API_URL'), verb)
        auth_username = Config.get('NISMOD_DB_API_USERNAME')
        auth_password = Config.get('NISMOD_DB_API_PASSWORD')
        if not 'export_format' in api_params:
            # Add in GeoJSON as the default export format
            api_params['export_format'] = 'geojson'
        try:
            r = requests.get(api_url, params=api_params, auth=(auth_username, auth_password))
            r.raise_for_status()
            target_geojson = r.json()
            if not 'type' in target_geojson and collection_name in target_geojson:
                # Potentially multiple FeatureCollections, so extract the one we want
                target_geojson = target_geojson[collection_name] 
            geojson_gdf = gpd.GeoDataFrame.from_features(target_geojson)
        except requests.exceptions.HTTPError as httperr:
            self.logger.warning('HTTP error from NISMOD-DB++ call to {} - {}'.format(api_url, httperr))
        except ValueError as err:
            self.logger.warning('NISMOD-DB++ call to {} returned invalid JSON - error was {}'.format(api_url, err))
            raise
        return geojson_gdf

    def validate_geodataframe(self, gdf, crs=Config.get('BRITISH_NATIONAL_GRID')):
        """
        |  Do some simple checks on a GeoDataFrame i.e. correct type and projection as specified
        |  Keyword arguments:
        |  gdf     -- GeoDataFrame to validate
        |  crs     -- Projection, defaults to EPSG:27700 (British National Grid)
        |
        |  Returns:
        |  True if checks passed
        """
        validated = False
        if not isinstance(gdf, gpd.GeoDataFrame):
            # Not a GeoDataFrame at all
            self.logger.warning('No GeoDataFrame containing existing dataset supplied for extract generator')
        elif gdf.crs['init'] != crs:
            # Wrong projection
            self.logger.warning('Point dataset supplied, but is not in British National Grid projection')
        else:
            validated = True
        return validated
