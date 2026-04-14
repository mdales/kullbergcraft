import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

def make_circle(radius, dtype=bool):
    size = 2 * radius + 1
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x**2 + y**2 <= radius**2
    return mask.astype(dtype)

def find_lakes(
    dem_path: Path,
    lcc_path: Path,
    output_path: Path,
) -> None:
    with (
        yg.read_rasters(dem_path.glob("*.tif")) if dem_path.is_dir() else yg.read_raster(dem_path) as dem,
        yg.read_raster(lcc_path) as lcc,
    ):
        water = lcc.isin([
            6, 61, 62, # water
            #2, # wetlands
        ])
        dem_water = water * dem
        elevations, counts = dem_water.unique(return_counts=True)
        df = pd.DataFrame(zip(elevations, counts), columns=["elevation", "count"])
        df = df[df.elevation != 0] # get rid of all the non-water areas
        df = df[df['count'] > 10000] # get only large areas of water
        lake_elevations = set(df.elevation)


        buffer_kernel = make_circle(20, np.float32)

        lakes = []
        for _, row in df.iterrows():
            elevation = row.elevation

            known_water_at_elevation = water * (dem == elevation)
            buffered_known_water_at_elevation = known_water_at_elevation.astype(yg.DataType.Float32).conv2d(buffer_kernel)

            # lakes = lakes + ((dem == elevation) * buffered_known_water_at_elevation)
            lakes.append( buffered_known_water_at_elevation)


        # lakes = dem.isin(lake_elevations)

        # remove single pixels
#         kernel = np.array([
#             [0, 1, 0],
#             [1, 10, 1],
#             [0, 1, 0],
#         ], dtype=np.float32)
#         filted_lakes = lakes.astype(yg.DataType.Float32).conv2d(kernel) > 12
        filted_lakes = yg.sum(lakes)

        filted_lakes.to_geotiff(output_path, parallelism=True)

@snakemake_compatible(mapping={
    "dem_path": "input.dem",
    "lcc_path": "input.lcc",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dtm',
        type=Path,
        help='dtm raster',
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
