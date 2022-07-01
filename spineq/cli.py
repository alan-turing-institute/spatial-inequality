import argparse

from spineq.data_fetcher import extract_la_data
from spineq.mappings import lad20cd_to_lad20nm, lad20nm_to_lad20cd


def spineq_download():
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
