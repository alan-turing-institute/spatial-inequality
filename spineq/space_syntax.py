from functools import partial
from pathlib import Path
from typing import Callable, Iterable, Optional, Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry.polygon import Polygon
from sklearn.linear_model import LinearRegression, PoissonRegressor
from tqdm import tqdm

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


def get_dft_data(
    lad20cd: str, dft_path: Union[str, Path], dft_year: int = 2019
) -> gpd.GeoDataFrame:
    """Load DfT traffic count data for a local authority

    Parameters
    ----------
    lad20cd : str
        Code for the local authority to get data for
    dft_path : Union[str, Path]
        Path to DfT traffic counts data
    dft_year : int , optional
        Use traffic count data for this year

    Returns
    -------
    gpd.GeoDataFrame
        DfT traffic count data
    """
    la = get_la_shape(lad20cd)
    dft = pd.read_csv(dft_path)
    dft = dft[dft["year"] == dft_year]
    dft = gpd.GeoDataFrame(
        dft,
        geometry=gpd.points_from_xy(dft["easting"], dft["northing"]),
        crs="epsg:27700",
    )
    dft.rename(columns={"id": "dft_id"}, inplace=True)
    dft = within_or_crosses(dft, la.geometry)
    return dft


def match_dft_ss(
    dft: pd.DataFrame, ss: gpd.GeoDataFrame, offset: float = 10, tolerance: float = 50
) -> gpd.GeoDataFrame:
    """Find the line segments in the space syntax data ss that are closest to the
    traffic measurement points in dft.

    Inspired by https://medium.com/@brendan_ward/6113c94e59aa

    Parameters
    ----------
    dft : pd.DataFrame
        Traffic point measurements
    ss : gpd.GeoDataFrame
        Space syntax segments
    offset : float, optional
        Bounding box around dft points - only keep space syntax segments that are within
        this bounding box of a dft point, by default 50
    tolerance : float, optional
        Exclude dft - space syntax matches with more than this distance between them,
        by default 50

    Returns
    -------
    gpd.GeoDataFrame
        dft points joined with the data of its nearest space syntax segment
    """
    ss.sindex  # Create spatial index (makes computation faster later)

    # all space syntax (ss) segments that intersect DfT measurement points
    # (within offset metres east/north of measurement point):
    bbox = dft.bounds + [-offset, -offset, offset, offset]
    hits = bbox.apply(lambda row: list(ss.sindex.intersection(row)), axis=1)

    # convert hits to flat list (row cotaining list of matches, to rows each
    # containing 1 match)
    hits = pd.DataFrame(
        {
            # index of point in dft
            "pt_idx": np.repeat(hits.index, hits.apply(len)),
            # index of line segment in ss
            "line_idx": np.concatenate(hits.values),
        }
    )

    # Join ss and dft based on matched indices
    hits = hits.join(ss.reset_index(drop=True), on="line_idx")
    hits = hits.join(dft.rename(columns={"geometry": "point"}), on="pt_idx")
    hits = gpd.GeoDataFrame(hits, geometry="geometry", crs=dft.crs)

    # calculate distances between points and matched line segments
    hits["snap_dist"] = hits.geometry.distance(gpd.GeoSeries(hits.point))
    # discard any hits with more than tolerance metres between dft point
    # and ss segment
    hits = hits.loc[hits.snap_dist <= tolerance]

    # Select closest dft point and ss segment match
    hits = hits.sort_values(by=["snap_dist"])
    closest = hits.groupby("pt_idx").first()

    return gpd.GeoDataFrame(closest, geometry="geometry")


def fit_traffic_model(
    traffic_counts: Union[np.ndarray, pd.Series], nach: Union[np.ndarray, pd.Series]
) -> tuple[float, float]:
    """Fit traffic counts to space syntax (normalised angular choice). Fits
    the model traffic_counts = exp(alpha + beta * nach ) using Poisson regression.

    Parameters
    ----------
    traffic_counts : Union[np.ndarray, pd.Series]
        Array or series of traffic counts

    nach : Union[np.ndarray, pd.Series]
        Array or series of normalised angular choice values at each traffic countt
        point

    Returns
    -------
    tuple(float, float)
        alpha (intercept) and beta (coefficient) parameters in
        traffic_counts = exp(alpha + beta * nach)
    """
    mask = (nach > 0) & (traffic_counts > 0)
    X = nach[mask].values.reshape(-1, 1)
    y = traffic_counts[mask]

    mdl = PoissonRegressor()
    mdl.fit(X, y)
    alpha = mdl.intercept_
    beta = mdl.coef_[0]
    print(f"alpha = {alpha}, beta = {beta}")
    print("Model D^2", mdl.score(X, y))

    return alpha, beta


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
    for oa_name in tqdm(oa.index):
        oa_segments = within_or_crosses(
            segments, oa.loc[oa_name, "geometry"], with_crosses=with_crosses
        )
        oa_summary.append(oa_segments[stat_column].agg(agg_fn))

    if callable(agg_fn):
        name = stat_column + agg_fn.__name__
    else:
        name = stat_column + agg_fn
    return pd.Series(oa_summary, index=oa.index, name=name)


def template_nach_to_traffic_fn(
    nach: Union[np.ndarray, pd.Series],
    alpha: float = 3.77147764,
    beta: float = np.exp(8.620081815759415),
) -> Union[np.ndarray, pd.Series]:
    """Convert angular choice values to a traffic proxy with equation:
    traffic = exp(alpha + beta * nach)
    Defaults from model fit on Newcastle 2019 DFT counts.

    Parameters
    ----------
    nach : Union[np.ndarray, pd.Series]
        Normalised angular choice values
    alpha : float, optional
        alpha parameter in traffic = exp(alpha + beta * nach)
    beta : float, optional
        beta parameter in traffic = exp(alpha + beta * nach)

    Returns
    -------
    Union[np.ndarray, pd.Series]:
        Angular choice converted to traffic proxy
    """
    return np.exp(alpha + beta * nach)


def space_syntax_traffic_proxy(
    lad20cd: str = "E08000021",
    ss_segments_path: Optional[Union[str, Path]] = Path(
        RAW_DIR, "space_syntax/TyneandWear_geojson.geojson"
    ),
    dft_path: Optional[Union[str, Path]] = Path(
        RAW_DIR, "dft/dft_traffic_counts_aadf.csv"
    ),
    nach_to_traffic_fn: Optional[Callable] = template_nach_to_traffic_fn,
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
    dft_path : Union[str, Path], optional
        Path to DfT traffic count data
    nach_to_traffic_fn : Callable, optional
        Function to convert AC_NACH values to proxy traffic count. Or return AC_NACH
        directly if None. Takes a series/array of ac_nach values as its only input.

    Returns
    -------
    pd.Series
        traffic proxy for each output area computed from AC_NACH
    """
    segments = gpd.read_file(ss_segments_path)

    try:
        dft = get_dft_data(lad20cd, dft_path)
    except FileNotFoundError:
        dft = None
        print(f"No DfT data at {dft_path}, will use default proxy function")

    if dft is not None:
        dft_ss = match_dft_ss(dft, segments)
        alpha, beta = fit_traffic_model(
            dft_ss["all_motor_vehicles"], dft_ss["AC__NACH"]
        )
        nach_to_traffic_fn = partial(
            template_nach_to_traffic_fn, alpha=alpha, beta=beta
        )

    max_ac_nach = oa_segment_summary(segments, lad20cd, "AC__NACH", "max")
    max_ac_nach.name = "traffic"
    max_ac_nach.fillna(0, inplace=True)

    if nach_to_traffic_fn is None:
        return max_ac_nach

    return nach_to_traffic_fn(max_ac_nach)


if __name__ == "__main__":
    lad20cd = "E08000037"  # "E08000021"  "E08000037"
    traffic = space_syntax_traffic_proxy(lad20cd=lad20cd)
    traffic.to_csv(Path(PROCESSED_DIR, lad20cd, "traffic.csv"))
    print(traffic.describe())
