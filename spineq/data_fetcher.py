import os
from io import BytesIO
import zipfile
import time

import warnings

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
    oa11cd = tyne_oa["oa11cd"].values
    
    # Weight for each point of interest (in this case population estimate for 
    # each output area)
    poi_weight = tyne_oa["Population"].values
    
    return {"poi_x": poi_x,
            "poi_y": poi_y,
            "poi_weight": poi_weight,
            "oa11cd": oa11cd,
            }
    

def load_gdf(path, epsg=27700):
    gdf = gpd.read_file(path)
    gdf.to_crs(epsg=epsg, inplace=True)
    return gdf


def download_la(overwrite=False):
    save_path = RAW_DIR + "/la/la.shp"
    if os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)
    url = "https://ons-inspire.esriuk.com/arcgis/rest/services/Administrative_Boundaries/Local_Athority_Districts_December_2018_Boundaries_GB_BFC/MapServer/0/query?where=UPPER(lad18nm)%20like%20'%25NEWCASTLE%20UPON%20TYNE%25'&outFields=*&outSR=27700&f=json"
    return query_ons_records(url, save_path=save_path)


def download_oa(overwrite=False):
    save_path = RAW_DIR + "/oa/oa.shp"
    if os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)
    url = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/OA_DEC_2011_EW_BFC/FeatureServer/0/query?where=1%3D1&outFields=*&geometry=-2.6%2C54.4%2C-0.7%2C55.3&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=27700&f=json"
    return query_ons_records(url, save_path=save_path)


def download_centroids(overwrite=False):
    save_path = RAW_DIR + "/centroids.csv"
    if os.path.exists(save_path) and not overwrite:
        return pd.read_csv(save_path)
    
    url = "https://ons-inspire.esriuk.com/arcgis/rest/services/Census_Boundaries/Output_Area_December_2011_Centroids/MapServer/0/query?where=1%3D1&outFields=*&geometry=-2.6%2C54.4%2C-0.7%2C55.3&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=27700&f=json"
    centroids = query_ons_records(url)
    centroids["X"] = centroids["geometry"].x
    centroids["Y"] = centroids["geometry"].y
    
    df = pd.DataFrame(index=centroids.index)
    df["X"] = centroids["X"]
    df["Y"] = centroids["Y"]
    df["oa11cd"] = centroids["oa11cd"]
    
    df.to_csv(save_path, index=False)
    
    return df


def download_populations(overwrite=False):
    save_path_total = RAW_DIR + "/population_total.csv"
    save_path_ages = RAW_DIR + "/population_ages.csv"
    if (os.path.exists(save_path_total) and os.path.exists(save_path_ages)
        and not overwrite):
        return pd.read_csv(save_path_total), pd.read_csv(save_path_ages)
    
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
                       thousands=",")

    df_total = df[["OA11CD", "All Ages"]]
    df_total.rename(columns={"All Ages": "population"}, inplace=True)
    df_total.to_csv(save_path_total, index=False)

    df_ages = df.drop(["All Ages", "LSOA11CD"], axis=1)
    df_ages.rename(columns={"90+": 90}, inplace=True)
    df_ages.to_csv(save_path_ages, index=False)
    
    return df_total, df_ages


def download_workplace(overwrite=False):
    save_path = RAW_DIR + "/workplace.csv"
    if overwrite:
        warnings.warn("Not possible to download workplace data directly. Go to https://www.nomisweb.co.uk/query/construct/summary.asp?reset=yes&mode=construct&dataset=1228&version=0&anal=1&initsel=")

    return pd.read_csv(save_path, thousands=',')


def download_data_files(overwrite=False):
    print("LOCAL AUTHORITY BOUNDARIES")
    la = download_la(overwrite=overwrite)
    print(la.head())
    
    print("OUTPUT AREA BOUNDARIES")
    oa = download_oa(overwrite=overwrite)
    print(oa.head())
    
    print("OUTPUT AREA CENTROIDS")
    centroids = download_centroids(overwrite=overwrite)
    print(centroids.head())
    
    print("OUTPUT AREA POPULATIONS")
    population_total, population_ages = download_populations(overwrite=overwrite)
    print(population_total.head())
    
    print("WORKPLACE")
    workplace = download_workplace(overwrite=overwrite)
    print(workplace.head())


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


def columns_to_lowercase(df):
    """Convert all columns with string names in a dataframe to lowercase.
    
    Arguments:
        df {pd.DataFrame} -- pandas dataframe
        
    Returns:
        pd.DataFrame -- input dataframe with columns converted to lowercase
    """
    
    cols_to_rename = df.columns[[type(col) is str for col in df.columns]]
    cols_replace_dict = {name: name.lower() for name in cols_to_rename}

    return df.rename(columns=cols_replace_dict)

    
def process_data_files(overwrite=False):
    la = download_la(overwrite=overwrite)
    oa = download_oa(overwrite=overwrite)
    centroids = download_centroids(overwrite=overwrite)
    workplace = download_workplace(overwrite=overwrite)
    population_total, population_ages = download_populations(overwrite=overwrite)
        
    # OAs to keep: those that intersect LA geometry
    for _, row in la.iterrows():
        oa = oa[oa.intersects(row["geometry"])]
    
    if len(oa) == 0:
        raise ValueError("None of {} OAs intersect any of {} LAs".format(len(oa),
                                                                         len(la)))
    
    oa = columns_to_lowercase(oa)
    oa = oa[["oa11cd", "geometry"]]
    os.makedirs(PROCESSED_DIR + "/oa_shapes", exist_ok=True)
    oa.to_file(PROCESSED_DIR + "/oa_shapes/oa_shapes.shp")
    oa_to_keep = oa["oa11cd"].values
    print("OA:", len(oa), "rows")
    
    # filter centroids
    centroids = columns_to_lowercase(centroids)
    centroids = centroids[centroids["oa11cd"].isin(oa_to_keep)]
    centroids = centroids[["oa11cd", "x", "y"]]
    centroids.to_csv(PROCESSED_DIR + "/centroids.csv", index=False)
    print("Centroids:", len(centroids), "rows")
    
    # filter population data
    population_total = columns_to_lowercase(population_total)
    population_total = population_total[population_total["oa11cd"].isin(oa_to_keep)]
    population_total = population_total[["oa11cd", "population"]]
    population_total.to_csv(PROCESSED_DIR + "/population_total.csv", index=False)
    print("Total Population:", len(population_total), "rows")

    population_ages = columns_to_lowercase(population_ages)    
    population_ages = population_ages[population_ages["oa11cd"].isin(oa_to_keep)]
    population_ages.to_csv(PROCESSED_DIR + "/population_ages.csv", index=False)
    print("Population by Age:", len(population_ages), "rows")
        
    # filter worokplace
    workplace = columns_to_lowercase(workplace)
    workplace = workplace[workplace["oa11cd"].isin(oa_to_keep)]
    workplace.to_csv(PROCESSED_DIR + "/workplace.csv", index=False)
    print("Place of Work:", len(workplace), "rows")
        
    if not (len(oa) == len(centroids) and len(oa) == len(population_total)
            and len(oa) == len(population_ages) and len(oa) == len(workplace)):
        warnings.warn("Lengths of processed data don't match, optimisation will fail!")
        

def get_oa_stats():
    """Get output area population (for each age) and place of work statistics.
    
    Returns:
        dict -- Dictionary of dataframe with keys population_ages and workplace.
    """
    population_ages = pd.read_csv(PROCESSED_DIR + "/population_ages.csv",
                                  index_col="oa11cd")
    population_ages.columns = population_ages.columns.astype(int)
    
    workplace = pd.read_csv(PROCESSED_DIR + "/workplace.csv",
                            index_col="oa11cd")
    workplace = workplace["workers"]
    
    return {"population_ages": population_ages, "workplace": workplace}


def get_oa_centroids():
    """Get output area population weighted centroids
    
    Returns:
        pd.DataFrame -- Dataframe with index oa11cd and columns x and y.
    """
    return pd.read_csv(PROCESSED_DIR + "/centroids.csv", index_col="oa11cd")
    

if __name__ == "__main__":
    process_data_files()
