import argparse
from pathlib import Path

from scipy.ndimage import generic_filter
from scipy import stats
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible


def mode_nonzero(values):
    center_idx = len(values) // 2
    if values[center_idx] != 0:
        return values[center_idx]

    nonzero = values[values != 0]
    if len(nonzero) == 0:
        return 0

    return stats.mode(nonzero, keepdims=False).mode

def make_land(
    dem_path: Path,
    lcc_path: Path,
    output_path: Path,
) -> None:
    with yg.read_raster(lcc_path) as lcc:
        filtered_lcc = yg.where(lcc.isin((6, 61, 62, 5, 51, 52, 53)), 0, lcc)
        xsize, ysize = lcc.dimensions
        data = filtered_lcc.read_array(0, 0, xsize, ysize)
        res = generic_filter(data, mode_nonzero, size=3)
        with yg.from_array(res, (lcc.area.left, lcc.area.top), lcc.projection) as refined:
            refined.to_geotiff(output_path)
            # with yg.read_rasters(dem_path.glob("*.tif")) as dem:
            #     with ReprojectedRasterLayer(refined, dem.map_projection, yg.ResamplingMethod.Nearest) as rescaled:
            #         rescaled.to_geotiff(output_path)

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
        help='DEM raster',
        required=True,
        dest='dem_path',
    )
    parser.add_argument(
        '--lcc',
        type=Path,
        help='10M LCC raster',
        required=True,
        dest='lcc_path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of directory for combined rasters raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()
    make_land(
        args.dem_path,
        args.lcc_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()

