import argparse
from pathlib import Path

import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

def align_nmd_with_dem(
    dem_path: Path,
    lcc_path: Path,
    output_path: Path,
) -> None:
    with yg.read_rasters(dem_path.glob("*.tif")) as dem:
        with yg.read_raster_like(
            lcc_path,
            dem,
            yg.ResamplingMethod.Nearest,
        ) as lcc:
            lcc.set_window_for_intersection(dem.area)
            lcc.to_geotiff(output_path)

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
        help='Path of aligned raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()

    align_nmd_with_dem(
        args.dem_path,
        args.lcc_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()
