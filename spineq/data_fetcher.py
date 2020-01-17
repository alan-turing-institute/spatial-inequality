import os
from io import BytesIO
import zipfile
import time

import requests

import pandas as pd
import geopandas as gpd
import fiona

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def get_data():
    tyne_oa = gpd.read_file(PROCESSED_DIR + "/tyne_oa")
    
    # Location of points of interest (in this case output area population
    # weighted centroids)
    poi_x = tyne_oa["X"].values
    poi_y = tyne_oa["Y"].values
    
    # Weight for each point of interest (in this case population estimate for 
    # each output area)
    poi_weight = tyne_oa["Population"].values
    
    return {"poi_x": poi_x,
            "poi_y": poi_y,
            "poi_weight": poi_weight}
    

def load_gdf(path, epsg=27700):
    gdf = gpd.read_file(path)
    gdf.to_crs(epsg=epsg, inplace=True)
    return gdf


def get_la():
    save_path = RAW_DIR + "/la/la.shp"
    url = "https://ons-inspire.esriuk.com/arcgis/rest/services/Administrative_Boundaries/Local_Athority_Districts_December_2018_Boundaries_GB_BFC/MapServer/0/query?where=UPPER(lad18nm)%20like%20'%25NEWCASTLE%20UPON%20TYNE%25'&outFields=*&outSR=27700&f=json"
    return query_ons_records(url, save_path=save_path)


def get_oa():
    save_path = RAW_DIR + "/oa/oa.shp"
    url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/OA_DEC_2011_EW_BFC/FeatureServer/0/query?where=1%3D1&outFields=*&geometry=-2.160%2C54.936%2C-1.052%2C55.074&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=27700&f=json"

    return query_ons_records(url, save_path=save_path)


def get_centroids():
    save_path = RAW_DIR + "/centroids/centroids.shp"
    url = "https://ons-inspire.esriuk.com/arcgis/rest/services/Census_Boundaries/Output_Area_December_2011_Centroids/MapServer/0/query?where=1%3D1&outFields=*&geometry=-2.177%2C54.917%2C-1.069%2C55.055&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=27700&f=json"
    centroids = query_ons_records(url, save_path=save_path)
    centroids["X"] = centroids["geometry"].x
    centroids["Y"] = centroids["geometry"].y
    
    return centroids


def get_populations(overwrite=False):
    save_path = RAW_DIR + "/populations.csv"
    if os.path.exists(save_path) and not overwrite:
        return pd.read_csv(save_path)
    
    url = "https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2fcensusoutputareaestimatesinthenortheastregionofengland%2fmid2018sape21dt10d/sape21dt10dmid2018northeast.zip"
    r = requests.get(url)
    
    zip_file = zipfile.ZipFile(BytesIO(r.content))
    
    file_name = None
    for name in zip_file.namelist():
        if ".xlsx" in name:
            file_name = name
            break
    
    if not file_name:
        raise ValueError("No .xlsx found in zip archive")
    
    xl_file = zip_file.open(file_name)
    
    df = pd.read_excel(xl_file,
                       sheet_name="Mid-2018 Persons",
                       skiprows=4,
                       usecols=("OA11CD", "LSOA11CD", "All Ages"))

    df.rename(columns={"All Ages": "Population"},
              inplace=True)
    
    df.to_csv(save_path, index=False)
    
    return df


def make_data_files():
    print("LOCAL AUTHORITY BOUNDARIES")
    la = get_la()
    
    print("OUTPUT AREA BOUNDARIES")
    oa = get_oa()

    print("OUTPUT AREA CENTROIDS")
    centroids = get_centroids()
    
    print("OUTPUT AREA POPULATIONS")
    populations = get_populations()
    
    print("MERGING")
    oa = oa[oa.intersects(la["geometry"])]
    
    print(centroids.head())
    centroids = centroids.merge(populations,
                                left_on='oa11cd',
                                right_on='OA11CD')

    oa = oa.merge(centroids[["X", "Y", "oa11cd", "Population"]],
                  how="left", on="oa11cd")

    print("SAVING")
    save_dir = DATA_DIR + "/processed"
    os.makedirs(save_dir, exist_ok=True)
    
    select_cols = ["oa11cd", "lad11cd", "geometry", "X", "Y", "Population"]
    oa[select_cols].to_file(save_dir + "/processed.shp")
    
    print("DONE!")
    
    return oa


def query_ons_records(base_query, time_between_queries=1,
                      save_path=None, overwrite=False):
    if save_path and os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)
    
    offset_param = "&resultOffset={}"
    count_param = "&returnCountOnly=true"

    r = requests.get(base_query + count_param)
    j = r.json()
    n_records_to_query = j["count"]
    
    if n_records_to_query > 0:
        print("This query returns", n_records_to_query, "records.")
    else:
        raise ValueError("Input query returns no records.")

    n_queried_records = 0
    all_records = None
    while n_queried_records < n_records_to_query:
        print("PROGRESS:", n_queried_records, "out of", n_records_to_query, "records")
        start_time = time.time()
        
        print("Querying... ", end="")
        
        try:
            r = requests.get(base_query +
                             offset_param.format(n_queried_records))
            
        except requests.exceptions.Timeout:
            print("timeout, retrying...")
            for i in range(10):
                print("attempt", i+1)
                try:
                    r = requests.get(base_query +
                                     offset_param.format(n_queried_records))
                    break
                except requests.exceptions.Timeout:
                    r = None
                    continue
            if not r:
                raise requests.exceptions.Timeout("FAILED - timeout.")
                         
        j = r.json()

        n_new_records = len(j["features"])
        n_queried_records += n_new_records
        print("Got", n_new_records, "records.")
        
        if n_new_records > 0:    
            b = bytes(r.content)
            with fiona.BytesCollection(b) as f:
                crs = f.crs
                new_records = gpd.GeoDataFrame.from_features(f, crs=crs)
            
            if all_records is None:
                all_records = new_records.copy(deep=True)
            else:
                all_records = all_records.append(new_records)
                
        if ("exceededTransferLimit" in j.keys() and
            j["exceededTransferLimit"] is True):
            end_time = time.time()
            if end_time - start_time < time_between_queries:
                time.sleep(time_between_queries + start_time - end_time)
                continue
        else:
            print("No more records to query.")
            break
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        all_records.to_file(save_path)

    return all_records
