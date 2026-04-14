import argparse
from pathlib import Path

import laspy
import numpy as np
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

RESOLUTION = 1.0

def points_to_dsm(
    laz_path: Path,
    output_path: Path,
) -> None:

    laz_files = list(laz_path.glob("**/*.laz"))

    # First pass: find overall bounds
    min_x, max_x = np.inf, -np.inf
    min_y, max_y = np.inf, -np.inf

    for path in laz_files:
        las = laspy.read(path)
        min_x = min(min_x, las.x.min())
        max_x = max(max_x, las.x.max())
        min_y = min(min_y, las.y.min())
        max_y = max(max_y, las.y.max())

    left = np.floor(min_x)
    top = np.ceil(max_y)
    NCOLS = int(np.ceil((max_x - left) / RESOLUTION))
    NROWS = int(np.ceil((top - min_y) / RESOLUTION))

    print(f"Grid: {NCOLS} x {NROWS}, origin ({left}, {top})")

    # Second pass: rasterize
    grid = np.full((NROWS, NCOLS), -np.inf)

    water = np.full((NROWS, NCOLS), -np.inf)

    for path in laz_files:
        las = laspy.read(path)

        mask = np.isin(las.classification, [2, 17])
        x = las.x[mask]
        y = las.y[mask]
        z = las.z[mask]

        col = ((x - left) / RESOLUTION).astype(int)
        row = ((top - y) / RESOLUTION).astype(int)

        valid = (col >= 0) & (col < NCOLS) & (row >= 0) & (row < NROWS)
        np.maximum.at(grid.ravel(), (row[valid] * NCOLS + col[valid]), z[valid])

        mask = np.isin(las.classification, [9])
        x = las.x[mask]
        y = las.y[mask]
        z = las.z[mask]

        col = ((x - left) / RESOLUTION).astype(int)
        row = ((top - y) / RESOLUTION).astype(int)

        valid = (col >= 0) & (col < NCOLS) & (row >= 0) & (row < NROWS)
        np.maximum.at(water.ravel(), (row[valid] * NCOLS + col[valid]), z[valid])


    grid[grid == -np.inf] = np.nan
    grid_sans_water = np.where(water==-np.inf, grid, np.nan)

    projection = yg.MapProjection("EPSG:3006", 1.0, -1.0)
    with yg.from_array(grid_sans_water, (left, top), projection) as r:
        r.to_geotiff(output_path)
#
#     water[water == -np.inf] = np.nan
#     with yg.from_array(water, (left, top), projection) as w:
#         w.to_geotiff('data/water.tif')


@snakemake_compatible(mapping={
    "laz_path": "input.laz_directory",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--laz_path',
        type=Path,
        help='directory of laz files',
        required=True,
        dest='laz_path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of lake DSM raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()

    points_to_dsm(
        args.laz_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()
