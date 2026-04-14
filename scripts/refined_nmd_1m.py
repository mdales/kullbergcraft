import argparse
from pathlib import Path

import numpy as np
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

def make_circle(radius, dtype=bool):
    size = 2 * radius + 1
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x**2 + y**2 <= radius**2
    return mask.astype(dtype)

def refined_nmd(
    lcc_path: Path,
    dtm_path: Path,
    lakes_path: Path,
    roads_path: Path,
    buildings_path: Path,
    output_path: Path,
) -> None:
    with (
        yg.read_raster(lcc_path) as lcc,
        yg.read_rasters(dtm_path.glob("*.tif")) if dtm_path.is_dir() else yg.read_raster(dtm_path) as dtm,
        yg.read_raster(lakes_path) as lakes,
        yg.read_shape_like(roads_path, lcc) as roads,
        yg.read_shape_like(buildings_path, lcc) as buildings,
    ):
        dtm_min = dtm.min()
        quantised_dtm = (dtm - dtm_min).floor()

        lake_levels = quantised_dtm * lakes
        water_level_kernel = make_circle(3, np.float32)
        kernel_total = water_level_kernel.sum()
        lake_levels_k = (lake_levels.astype(yg.DataType.Float32).conv2d(water_level_kernel) / kernel_total) == lake_levels
        lakes_n = yg.where(lakes > 0, lake_levels_k, 0)

        lcc_without_water_with_lakes = yg.where(lakes_n == 0, lcc, 61)
        lcc_without_water_with_lakes_and_roads = yg.where(roads == 0, lcc_without_water_with_lakes, 53)
        lcc_without_water_with_lakes_and_roads_and_buildings = yg.where(buildings == 0, lcc_without_water_with_lakes_and_roads, 51)
        lcc_without_water_with_lakes_and_roads_and_buildings.as_area(lcc).to_geotiff(output_path, parallelism=True)

@snakemake_compatible(mapping={
    "lcc_path": "input.lcc",
    "dtm_path": "input.dtm",
    "lakes_path": "input.lakes",
    "roads_path": "input.roads",
    "buildings_path": "input.buildings",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--lcc',
        type=Path,
        help='LCC raster',
        required=True,
        dest='lcc_path',
    )
    parser.add_argument(
        '--dtm',
        type=Path,
        help='dtm raster(s)',
        required=True,
        dest='dtm_path',
    )
    parser.add_argument(
        '--lakes',
        type=Path,
        help='lakes raster',
        required=True,
        dest='lakes_path',
    )
    parser.add_argument(
        '--roads',
        type=Path,
        help='roads geojson',
        required=True,
        dest="roads_path",
    )
    parser.add_argument(
        '--buildings',
        type=Path,
        help='buildins gpkg',
        required=True,
        dest="buildings_path",
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of directory for combined rasters raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()
    refined_nmd(
        args.lcc_path,
        args.dtm_path,
        args.lakes_path,
        args.roads_path,
        args.buildings_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()


