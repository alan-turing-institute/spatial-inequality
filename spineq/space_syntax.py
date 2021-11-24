from pathlib import Path
from typing import Callable, Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry.polygon import Polygon

from spineq import PROCESSED_DIR, RAW_DIR
from spineq.data_fetcher import get_la_shape, get_oa_shapes


def within_or_crosses(
    segments: gpd.GeoDataFrame, boundary: Polygon, with_crosses: bool = True
) -> gpd.GeoDataFrame:
    """Filter data frame of geometries (segments) to only include geometries that are
    within or cross a given boundary shape.

    Parameters
    ----------
    segments : gpd.GeoDataFrame
        Source data frame with geometries to filter
    boundary : Polygon
        Check whether geometries in segments are within or cross this boundary
    with_crosses : bool, optional
        If True also include geometries that cross the input boundary, by default True

    Returns
    -------
    gpd.GeoDataFrame
        Filtered data frame only incluuding geometries that cross or are within the
        input boundary
    """
    mask = segments.within(boundary)
    if with_crosses:
        mask = mask | segments.crosses(boundary)
    return segments[mask]


def oa_segment_summary(
    segments: gpd.GeoDataFrame,
    lad20cd: str,
    stat_column: str,
    agg_fn: Union[str, Callable],
    with_crosses: bool = True,
) -> pd.Series:
    """Take data for segments or points and compute a summary statistic of these for
    each output area in a local authority.

    Parameters
    ----------
    segments : gpd.GeoDataFrame
        Contains geometry (line segments or points) and column 'stat_column' to
        compute stats for in each output area (OA).
    lad20cd : str
        Local authority code to compute stats for. The `segments` input should contain
        data for this region.
    stat_column : str
        Column containing the values to summarise for each OA.
    agg_fn : Union[str, Callable]
        Function to use to compute the summary statistic for each OA,
        passed to pd.DataFrame.agg
    with_crosses : bool, optional
        If True, include segmentts that are both within the OA and cross the OA when
        computing the OA summarry statistic.
    """
    la = get_la_shape(lad20cd)
    oa = get_oa_shapes(lad20cd)
    # only keep segments that are in or cross the local authority
    # (to speed up computation)
    segments = within_or_crosses(segments, la.geometry, with_crosses=with_crosses)

    oa_summary = []
    for oa_name in oa.index:
        oa_segments = within_or_crosses(
            segments, oa.loc[oa_name, "geometry"], with_crosses=with_crosses
        )
        oa_summary.append(oa_segments[stat_column].agg(agg_fn))
    return pd.Series(oa_summary, index=oa.index)


def space_syntax_traffic_proxy(
    lad20cd: str = "E08000021",
    ss_segments_path: Union[str, Path] = Path(
        RAW_DIR, "space_syntax/TyneandWear_geojson.geojson"
    ),
) -> pd.Series:
    """Compute log(maximum normalised angular choice) in each output area of a local
    authority, which we use as a traffic proxy

    Parameters
    ----------
    lad20cd : str, optional
        Local authoritty code, by default "E08000021"
    ss_segments_path : Union[str, Path], optional
        Path to space syntax data including the column 'AC__NACH', by default
        Path( RAW_DIR, "space_syntax/TyneandWear_geojson.geojson" )

    Returns
    -------
    pd.Series
        log(Max AC_NACH) for each output area
    """
    segments = gpd.read_file(ss_segments_path)
    max_ac_nach = oa_segment_summary(segments, lad20cd, "AC__NACH", "max")
    # deal with possible log(0) and log(NaN) errors
    max_ac_nach.fillna(1e-6, inplace=True)
    max_ac_nach.replace(0, 1e-6, inplace=True)

    return np.log(max_ac_nach)


if __name__ == "__main__":
    lad20cd = "E08000021"
    max_ac_nach = space_syntax_traffic_proxy(lad20cd=lad20cd)
    max_ac_nach.to_csv(Path(PROCESSED_DIR, lad20cd, "traffic_proxy.csv"))
