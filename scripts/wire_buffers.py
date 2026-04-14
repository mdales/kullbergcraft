import argparse
from pathlib import Path

import fiona
import geopandas as gpd
import yirgacheffe as yg
from pyproj import Transformer
from shapely.geometry import box
from shapely.ops import transform
from snakemake_argparse_bridge import snakemake_compatible

def wire_buffers(
    template_path: Path,
    wires_path: Path,
    output_path: Path,
) -> None:
    with yg.read_raster(template_path) as template:
        template_area = template.area
        template_crs = template.projection.name

    kullberg_bbox = box(template_area.left, template_area.bottom, template_area.right, template_area.top)

    with fiona.open(wires_path, layer="ledningslinje") as src:
        file_crs = src.crs

    transformer = Transformer.from_crs(template_crs, file_crs, always_xy=True)
    kullberg_bbox_in_file_crs = transform(transformer.transform, kullberg_bbox)

    wires_data = gpd.read_file(wires_path, bbox=kullberg_bbox_in_file_crs, layer="ledningslinje")
    reprojected_wires_data = wires_data.to_crs(template_crs)
    trunk_lines = wires_data[wires_data.objekttyp == "Kraftledning stam"]

    # Buffer and clip in the target CRS
    trunk_lines["geometry"] = trunk_lines.apply(
        lambda row: row.geometry.buffer(row["lagesosakerhetplan"]),
        axis=1,
    )
    result = gpd.clip(trunk_lines, kullberg_bbox)
    result.to_file(output_path, driver="GPKG", layer="lagesosakerhetplan")


@snakemake_compatible(mapping={
    "template_path": "input.template",
    "wires_path": "input.wires",
    "output_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--template',
        type=Path,
        help='template raster',
        required=True,
        dest='template_path',
    )
    parser.add_argument(
        '--wires',
        type=Path,
        help='wires gpkg',
        required=True,
        dest='wires_path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of lake level raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()

    wire_buffers(
        args.template_path,
        args.wires_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()
