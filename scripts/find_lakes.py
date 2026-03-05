import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

def find_lakes(
    dem_path: Path,
    lcc_path: Path,
    output_path: Path,
) -> None:
    with (
        yg.read_rasters(dem_path.glob("*.tif")) as dem,
        yg.read_raster(lcc_path) as lcc,
    ):
        water = lcc.isin([
            6, 61, 62, # water
            2, # wetlands
        ])
        dem_water = water * dem
        elevations, counts = dem_water.unique(return_counts=True)
        df = pd.DataFrame(zip(elevations, counts), columns=["elevation", "count"])
        df = df[df.elevation != 0] # get rid of all the non-water areas
        df = df[df['count'] > 100000] # get only large areas of water
        lake_elevations = set(df.elevation)

        lakes = dem.isin(lake_elevations)

        # remove single pixels
        kernel = np.array([
            [0, 1, 0],
            [1, 10, 1],
            [0, 1, 0],
        ], dtype=np.float32)
        filted_lakes = lakes.astype(yg.DataType.Float32).conv2d(kernel) > 12

        filted_lakes.to_geotiff(output_path)

@snakemake_compatible(mapping={
    "dem_path": "input.dem",
    "lcc_path": "input.lcc",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dem',
        type=Path,
        help='dem raster',
        required=True,
        dest='dem_path',
    )
    parser.add_argument(
        '--lcc',
        type=Path,
        help='LCC raster',
        required=True,
        dest='lcc_path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of lake level raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()

    find_lakes(
        args.dem_path,
        args.lcc_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()
