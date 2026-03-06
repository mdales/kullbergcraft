import argparse
from pathlib import Path

import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

def refined_nmd(
    dem_path: Path,
    lcc_path: Path,
    lakes_path: Path,
    roads_path: Path,
    cameras_path: Path,
    output_path: Path,
) -> None:
    with (
        # yg.read_rasters(dem_path.glob("*.tif")) as dem,
        yg.read_raster(lcc_path) as lcc,
        yg.read_raster(lakes_path) as lakes,
        yg.read_shape_like(roads_path, lcc) as roads,
        yg.read_shape_like(cameras_path, lcc) as cameras,
    ):
        lcc_without_water_with_lakes = yg.where(lakes == 0, lcc, 61)
        lcc_without_water_with_lakes_and_roads = yg.where(roads == 0, lcc_without_water_with_lakes, 53)
        lcc_without_water_with_lakes_and_and_roads_cameras = yg.where(cameras != 0, 200, lcc_without_water_with_lakes_and_roads)
        lcc_without_water_with_lakes_and_and_roads_cameras.to_geotiff(output_path)

@snakemake_compatible(mapping={
    "dem_path": "input.dem",
    "lcc_path": "input.lcc",
    "lakes_path": "input.lakes",
    "roads_path": "input.roads",
    "cameras_path": "input.cameras",
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
        '--cameras',
        type=Path,
        help='Cameras point file',
        required=True,
        dest='cameras_path',
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
        args.dem_path,
        args.lcc_path,
        args.lakes_path,
        args.roads_path,
        args.cameras_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()


