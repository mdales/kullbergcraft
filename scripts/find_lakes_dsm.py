import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

yg.constants.YSTEP = 64

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
        yg.read_rasters(dem_path.glob("*.tif")) if dem_path.is_dir() else yg.read_raster(dem_path) as dem_with_nans,
        yg.read_raster(lcc_path) as lcc,
    ):
        lakes = (dem_with_nans * 0).nan_to_num(nan=1)
        water = lcc.isin([6, 61, 62]) # water land cover values in NMD

        buffer_kernel = make_circle(10, np.float32)
        buffered_water = water.astype(yg.DataType.Float32).conv2d(buffer_kernel) > 0
        near_water_lakes = lakes * buffered_water

        # remove single pixels
        kernel = np.array([
            [0, 1, 0],
            [1, 10, 1],
            [0, 1, 0],
        ], dtype=np.float32)
        kerneled_layer = near_water_lakes.astype(yg.DataType.Float32).conv2d(kernel)
        remove_noise = (kerneled_layer > 12) | (kerneled_layer == 4)

        remove_noise.to_geotiff(output_path, parallelism=True)

@snakemake_compatible(mapping={
    "dem_path": "input.dem",
    "lcc_path": "input.lcc",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dsm',
        type=Path,
        help='dsm raster',
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
