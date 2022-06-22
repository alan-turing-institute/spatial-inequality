import argparse
import json
import os
import time
import warnings
import zipfile
from io import BytesIO
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd
import requests

from spineq.config import PROCESSED_DIR, RAW_DIR


def load_gdf(path, epsg=27700):
    gdf = gpd.read_file(path)
    gdf.to_crs(epsg=epsg, inplace=True)
    return gdf


def download_la_shape(lad20cd="E08000021", overwrite=False):
    save_path = Path(PROCESSED_DIR, lad20cd, "la_shape", "la.shp")
    if os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)
    os.makedirs(save_path.parent, exist_ok=True)

    # From https://geoportal.statistics.gov.uk/datasets/
    #          ons::local-authority-districts-december-2020-uk-bgc/about
    base = (
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Local_Authority_Districts_December_2020_UK_BGC/FeatureServer/0"
    )
    query = (
        f"query?where=LAD20CD%20%3D%20%27{lad20cd}%27&outFields=*&outSR=27700&f=json"
    )
    url = f"{base}/{query}"
    la = query_ons_records(url, save_path=None)
    la = columns_to_lowercase(la)
    la = la[["geometry", "lad20cd", "lad20nm"]]
    la.to_file(save_path)
    return la


def lad20cd_to_lad11cd(lad20cd, mappings=None):
    if mappings is None:
        mappings = download_oa_mappings()
    return mappings[mappings.lad20cd == lad20cd]["lad11cd"].unique()


def lad11cd_to_lad20cd(lad11cd, mappings=None):
    if mappings is None:
        mappings = download_oa_mappings()
    return mappings[mappings.lad11cd == lad11cd]["lad20cd"].unique()


def lad20nm_to_lad20cd(lad20nm, mappings=None):
    if mappings is None:
        mappings = download_oa_mappings()
    return mappings[mappings.lad20nm == lad20nm]["lad20cd"].iloc[0]


def lad20cd_to_lad20nm(lad20cd, mappings=None):
    if mappings is None:
        mappings = download_oa_mappings()
    return mappings[mappings.lad20cd == lad20cd]["lad20nm"].iloc[0]


def lad11nm_to_lad11cd(lad11nm, mappings=None):
    if mappings is None:
        mappings = download_oa_mappings()
    return mappings[mappings.lad11nm == lad11nm]["lad11cd"].iloc[0]


def download_oa_shape(lad11cd="E08000021", lad20cd=None, overwrite=False):
    if isinstance(lad11cd, str):
        lad11cd = [lad11cd]
    if lad20cd is None:
        lad20cd = lad11cd_to_lad20cd(lad11cd[0])[0]

    save_path = Path(PROCESSED_DIR, lad20cd, "oa_shape", "oa.shp")
    if os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)
    os.makedirs(save_path.parent, exist_ok=True)

    oa = []
    for la in lad11cd:
        # From https://geoportal.statistics.gov.uk/datasets/
        #             ons::output-areas-december-2011-boundaries-ew-bgc-1/about
        url = (
            "https://ons-inspire.esriuk.com/arcgis/rest/services/Census_Boundaries/"
            "Output_Area_December_2011_Boundaries/FeatureServer/2/query?"
            f"where=lad11cd%20%3D%20'{la}'&outFields=*&outSR=27700&f=json"
        )
        oa.append(query_ons_records(url, save_path=None))

    oa = pd.concat(oa)
    oa = columns_to_lowercase(oa)
    oa = oa[["oa11cd", "geometry"]]
    oa.to_file(save_path)
    return oa


def download_oa_mappings(overwrite=False):
    save_path = Path(RAW_DIR, "oa_mappings.csv")
    if os.path.exists(save_path) and not overwrite:
        return pd.read_csv(save_path, dtype=str)

    # 2011
    # https://geoportal.statistics.gov.uk/datasets/ons::
    #      output-area-to-lower-layer-super-output-area-to-middle-layer-super-output
    #      -area-to-local-authority-district-december-2011-lookup-in-england-and-wales
    #      /about
    url = (
        "https://opendata.arcgis.com/api/v3/datasets/6ecda95a83304543bc8feedbd1a58303_0"
        "/downloads/data?format=csv&spatialRefId=4326"
    )
    df2011 = pd.read_csv(url)
    df2011.drop("ObjectId", axis=1, inplace=True)

    # 2020
    # https://geoportal.statistics.gov.uk/datasets/ons::
    #         output-area-to-lower-layer-super-output-area-to-middle-layer-super-output
    #         -area-to-local-authority-district-december-2020-lookup-in-england-and
    #         -wales/about
    url = (
        "https://opendata.arcgis.com/api/v3/datasets/65664b00231444edb3f6f83c9d40591f_0"
        "/downloads/data?format=csv&spatialRefId=4326"
    )
    df2020 = pd.read_csv(url)
    df2020.drop("FID", axis=1, inplace=True)

    merged = pd.merge(df2011, df2020, how="outer")
    merged = columns_to_lowercase(merged)
    merged.to_csv(save_path, index=False)
    return merged


def download_centroids(overwrite=False):
    save_path = Path(RAW_DIR, "centroids.csv")
    if os.path.exists(save_path) and not overwrite:
        return pd.read_csv(save_path)

    # From https://geoportal.statistics.gov.uk/datasets/ons::
    #              output-areas-december-2011-population-weighted-centroids-1/about
    url = (
        "https://opendata.arcgis.com/api/v3/datasets/b0c86eaafc5a4f339eb36785628da904_0"
        "/downloads/data?format=csv&spatialRefId=27700"
    )
    df = pd.read_csv(url)
    df = columns_to_lowercase(df)
    df = df[["oa11cd", "x", "y"]]
    df.to_csv(save_path, index=False)

    return df


def download_populations_region(url):
    r = requests.get(url)

    zip_file = zipfile.ZipFile(BytesIO(r.content))
    file_name = next((name for name in zip_file.namelist() if ".xlsx" in name), None)

    if not file_name:
        raise ValueError("No .xlsx found in zip archive")

    xl_file = zip_file.open(file_name)

    df = pd.read_excel(
        xl_file, sheet_name="Mid-2019 Persons", skiprows=4, thousands=","
    )

    df_total = df[["OA11CD", "All Ages"]]
    df_total.rename(columns={"All Ages": "population"}, inplace=True)
    df_total = columns_to_lowercase(df_total)
    df_total = df_total[["oa11cd", "population"]]

    df_ages = df.drop(["All Ages", "LSOA11CD"], axis=1)
    df_ages.rename(columns={"90+": 90}, inplace=True)
    df_ages = columns_to_lowercase(df_ages)

    return df_total, df_ages


def download_populations(overwrite=False):
    save_path_total = Path(RAW_DIR, "population_total.csv")
    save_path_ages = Path(RAW_DIR, "population_ages.csv")
    if (
        os.path.exists(save_path_total)
        and os.path.exists(save_path_ages)
        and not overwrite
    ):
        return pd.read_csv(save_path_total), pd.read_csv(save_path_ages)

    # From https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/
    #              populationestimates/datasets/
    #              censusoutputareaestimatesinthenortheastregionofengland
    prefix = (
        "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/"
        "populationandmigration/populationestimates/"
        "datasets/censusoutputareaestimatesin"
    )
    region_names = [
        "thelondonregionofengland",
        "theyorkshireandthehumberregionofengland",
        "thesouthwestregionofengland",
        "theeastmidlandsregionofengland",
        "thesoutheastregionofengland",
        "theeastregionofengland",
        "thewestmidlandsregionofengland",
        "thenorthwestregionofengland",
        "thenortheastregionofengland",
        "wales",
    ]
    file_names = [
        "mid2019sape22dt10a/sape22dt10amid2019london.zip",
        "mid2019sape22dt10c/sape22dt10cmid2019yorkshireandthehumber.zip",
        "mid2019sape22dt10g/sape22dt10gmid2019southwest.zip",
        "mid2019sape22dt10f/sape22dt10fmid2019eastmidlands.zip",
        "mid2019sape22dt10i/sape22dt10imid2019southeast.zip",
        "mid2019sape22dt10h/sape22dt10hmid2019east.zip",
        "mid2019sape22dt10e/sape22dt10emid2019westmidlands.zip",
        "mid2019sape22dt10b/sape22dt10bmid2019northwest.zip",
        "mid2019sape22dt10d/sape22dt10dmid2019northeast.zip",
        "mid2019sape22dt10j/sape22dt10jmid2019wales.zip",
    ]
    region_urls = [
        f"{prefix}{r_name}/{f_name}" for r_name, f_name in zip(region_names, file_names)
    ]

    df_total = []
    df_ages = []
    for i, r in enumerate(region_urls):
        print("Dowloading region", i + 1, "out of", len(region_urls), ":", r)
        region_total, region_ages = download_populations_region(r)
        df_total.append(region_total)
        df_ages.append(region_ages)

    df_total = pd.concat(df_total)
    df_ages = pd.concat(df_ages)
    df_total.to_csv(save_path_total, index=False)
    df_ages.to_csv(save_path_ages, index=False)

    return df_total, df_ages


def download_workplace(overwrite=False):
    save_path = Path(RAW_DIR, "workplace.csv")
    if os.path.exists(save_path) and not overwrite:
        return pd.read_csv(save_path)

    url = "https://zenodo.org/record/6683974/files/workplace.csv"
    workplace = pd.read_csv(url)
    workplace.to_csv(save_path, index=False)
    return workplace


def download_uo_sensors(overwrite=False):
    save_path = Path(RAW_DIR, "uo_sensors", "uo_sensors.shp")
    if os.path.exists(save_path) and not overwrite:
        return gpd.read_file(save_path)

    query = "http://uoweb3.ncl.ac.uk/api/v1.1/sensors/json/?theme=Air+Quality"
    response = requests.get(query)
    sensors = json.loads(response.content)["sensors"]
    df = pd.DataFrame(sensors)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["Sensor Centroid Longitude"], df["Sensor Centroid Latitude"]
        ),
        crs="EPSG:4326",
    )
    # remove duplicate column - available as "geometry"
    gdf.drop("Location (WKT)", inplace=True, axis=1)
    gdf.rename(
        columns={
            "Sensor Height Above Ground": "h_ground",
            "Sensor Centroid Longitude": "longitude",
            "Raw ID": "id",
            "Broker Name": "broker",
            "Sensor Centroid Latitude": "latitude",
            "Ground Height Above Sea Level": "h_sea",
            "Third Party": "3rdparty",
            "Sensor Name": "name",
        },
        inplace=True,
    )
    gdf = columns_to_lowercase(gdf)
    # Convert to British National Grid CRS (same as ONS data)
    gdf = gdf.to_crs(epsg=27700)
    os.makedirs(save_path.parent, exist_ok=True)
    gdf.to_file(save_path)

    return gdf


def download_raw_data(overwrite=False):
    print("OUTPUT AREA TO LOCAL AUTHORITY MAPPINGS")
    mappings = download_oa_mappings(overwrite=overwrite)
    print(mappings.head())

    print("OUTPUT AREA CENTROIDS")
    centroids = download_centroids(overwrite=overwrite)
    print(centroids.head())

    print("OUTPUT AREA POPULATIONS")
    population_total, _ = download_populations(overwrite=overwrite)
    print(population_total.head())

    print("WORKPLACE")
    workplace = download_workplace(overwrite=overwrite)
    print(workplace.head())

    print("URBAN OBSERVATORY SENSORS")
    uo_sensors = download_uo_sensors(overwrite=overwrite)
    print(uo_sensors.head())


def query_ons_records(
    base_query, time_between_queries=1, save_path=None, overwrite=False
):
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
            r = requests.get(base_query + offset_param.format(n_queried_records))

        except requests.exceptions.Timeout as e:
            print("timeout, retrying...")
            for i in range(10):
                print("attempt", i + 1)
                try:
                    r = requests.get(
                        base_query + offset_param.format(n_queried_records)
                    )
                    break
                except requests.exceptions.Timeout:
                    r = None
                    continue
            if not r:
                raise requests.exceptions.Timeout("FAILED - timeout.") from e

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

        if "exceededTransferLimit" in j.keys() and j["exceededTransferLimit"] is True:
            end_time = time.time()
            if end_time - start_time < time_between_queries:
                time.sleep(time_between_queries + start_time - end_time)
                continue
        else:
            print("No more records to query.")
            break

    if save_path:
        os.makedirs(save_path.parent, exist_ok=True)
        print(all_records.columns)
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


def filter_oa(oa11cd, df):
    return df[df["oa11cd"].isin(oa11cd)]


def extract_la_data(lad20cd="E08000021", overwrite=False):
    print(f"Extracting data for {lad20cd}...")
    save_dir = Path(PROCESSED_DIR, lad20cd)
    os.makedirs(save_dir, exist_ok=True)

    la = download_la_shape(lad20cd=lad20cd, overwrite=overwrite)
    print("LA shape:", len(la), "rows")

    mappings = download_oa_mappings(overwrite=overwrite)
    oa_in_la = mappings.loc[mappings["lad20cd"] == lad20cd, "oa11cd"]
    print("OA in this LA (mappings):", len(oa_in_la), "rows")

    lad11cd = lad20cd_to_lad11cd(lad20cd, mappings)
    oa = download_oa_shape(lad11cd=lad11cd, overwrite=overwrite)
    print("OA shapes:", len(oa), "rows")

    # centroids
    centroids = download_centroids(overwrite=overwrite)
    centroids = filter_oa(oa_in_la, centroids)
    centroids.to_csv(Path(save_dir, "centroids.csv"), index=False)
    print("Centroids:", len(centroids), "rows")

    # population data
    population_total, population_ages = download_populations(overwrite=overwrite)
    population_total = filter_oa(oa_in_la, population_total)
    population_total.to_csv(Path(save_dir, "population_total.csv"), index=False)
    print("Total Population:", len(population_total), "rows")

    population_ages = columns_to_lowercase(population_ages)
    population_ages = filter_oa(oa_in_la, population_ages)
    population_ages.to_csv(Path(save_dir, "population_ages.csv"), index=False)
    print("Population by Age:", len(population_ages), "rows")

    # workplace
    workplace = download_workplace(overwrite=overwrite)
    workplace = filter_oa(oa_in_la, workplace)
    workplace.to_csv(Path(save_dir, "workplace.csv"), index=False)
    print("Place of Work:", len(workplace), "rows")

    if not (
        len(oa) == len(centroids)
        and len(oa) == len(population_total)
        and len(oa) == len(population_ages)
        and len(oa) == len(workplace)
    ):
        warnings.warn("Lengths of processed data don't match, optimisation will fail!")

    process_uo_sensors(lad20cd=lad20cd, overwrite=overwrite)


def process_uo_sensors(lad20cd="E08000021", overwrite=False):
    uo_sensors = download_uo_sensors(overwrite=overwrite)
    # Get sensors in local authority only
    la = get_la_shape(lad20cd=lad20cd)
    uo_sensors = uo_sensors[uo_sensors.intersects(la["geometry"])]
    if len(uo_sensors) > 0:
        # add OA each sensor is in
        oa = get_oa_shapes(lad20cd=lad20cd)
        uo_sensors = gpd.sjoin(uo_sensors, oa, how="left").rename(
            columns={"index_right": "oa11cd"}
        )

        save_path = Path(PROCESSED_DIR, lad20cd, "uo_sensors", "uo_sensors.shp")
        os.makedirs(save_path.parent, exist_ok=True)
        uo_sensors.to_file(save_path)
        print("Urban Observatory Sensors:", len(uo_sensors), "rows")
    else:
        print("No Urban Observatory sensors found in local authority", lad20cd)


def get_uo_sensors(lad20cd="E08000021"):
    path = Path(PROCESSED_DIR, lad20cd, "uo_sensors", "uo_sensors.shp")
    if not path.exists():
        extract_la_data(lad20cd)
    return gpd.read_file(path).set_index("id")


def get_oa_stats(lad20cd="E08000021"):
    """Get output area population (for each age) and place of work statistics.

    Returns:
        dict -- Dictionary of dataframe with keys population_ages and workplace.
    """
    pop_path = Path(PROCESSED_DIR, lad20cd, "population_ages.csv")
    work_path = Path(PROCESSED_DIR, lad20cd, "workplace.csv")
    if not pop_path.exists() or not work_path.exists():
        extract_la_data(lad20cd)

    population_ages = pd.read_csv(pop_path, index_col="oa11cd")
    population_ages.columns = population_ages.columns.astype(int)

    workplace = pd.read_csv(work_path, index_col="oa11cd")
    workplace = workplace["workers"]

    return {"population_ages": population_ages, "workplace": workplace}


def get_oa_centroids(lad20cd="E08000021"):
    """Get output area population weighted centroids

    Returns:
        pd.DataFrame -- Dataframe with index oa11cd and columns x and y.
    """
    path = Path(PROCESSED_DIR, lad20cd, "centroids.csv")
    if not path.exists():
        extract_la_data(lad20cd)
    return pd.read_csv(path, index_col="oa11cd")


def get_la_shape(lad20cd="E08000021"):
    path = Path(PROCESSED_DIR, lad20cd, "la_shape")
    if not path.exists():
        extract_la_data(lad20cd)
    return gpd.read_file(path).iloc[0]


def get_oa_shapes(lad20cd="E08000021"):
    path = Path(PROCESSED_DIR, lad20cd, "oa_shape")
    if not path.exists():
        extract_la_data(lad20cd)
    shapes = gpd.read_file(path)
    return shapes.set_index("oa11cd")


def main():
    parser = argparse.ArgumentParser(
        description="Save output area data for a local authority district"
    )
    parser.add_argument(
        "--lad20cd", help="LAD20CD (2020 local authority district code)", type=str
    )
    parser.add_argument(
        "--lad20nm", help="LAD20NM (2020 local authority district name)", type=str
    )
    parser.add_argument(
        "--overwrite",
        help="If set download and overwrite any pre-existing files",
        action="store_true",
    )
    args = parser.parse_args()

    if args.lad20cd:
        lad20cd = args.lad20cd
        lad20nm = lad20cd_to_lad20nm(lad20cd)
    elif args.lad20nm:
        lad20nm = args.lad20nm
        lad20cd = lad20nm_to_lad20cd(lad20nm)
    else:
        print("Either --lad20cd or --lad20nm must be given")

    print(f"Saving data for {lad20nm} ({lad20cd})")
    extract_la_data(lad20cd=lad20cd, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
