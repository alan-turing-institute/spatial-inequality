import numpy as np

from spineq.data.fetcher import download_oa_mappings, download_oa_shape

mappings = download_oa_mappings()


def point_to_oa(point):
    # TODO - this is slow (checks all England and Wales output areas)
    # could consider checking local authorities first, then only output areas
    # in appropriate local authority?
    oa_shape = download_oa_shape()
    oa11cd = oa_shape[oa_shape["geometry"].contains(point)].index
    if len(oa11cd) > 0:
        return oa11cd[0]
    return np.nan


def oa_to_la(oa11cd):
    return mappings.loc[mappings["oa11cd"] == oa11cd, "lad20cd"].iloc[0]


def la_to_oas(lad20cd):
    return mappings.loc[mappings["lad20cd"] == lad20cd, "oa11cd"]


def la_to_lsoas(lad20cd):
    return mappings.loc[mappings["lad20cd"] == lad20cd, "lsoa11cd"].unique()


def lsoa_to_oas(lsoa11cd):
    return mappings.loc[mappings["lsoa11cd"] == lsoa11cd, "oa11cd"]


def lad20cd_to_lad11cd(lad20cd):
    return mappings[mappings.lad20cd == lad20cd]["lad11cd"].unique()


def lad11cd_to_lad20cd(lad11cd):
    return mappings[mappings.lad11cd == lad11cd]["lad20cd"].unique()


def lad20nm_to_lad20cd(lad20nm):
    return mappings[mappings.lad20nm == lad20nm]["lad20cd"].iloc[0]


def lad20cd_to_lad20nm(lad20cd):
    return mappings[mappings.lad20cd == lad20cd]["lad20nm"].iloc[0]


def lad11nm_to_lad11cd(lad11nm):
    return mappings[mappings.lad11nm == lad11nm]["lad11cd"].iloc[0]
