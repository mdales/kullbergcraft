import argparse
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import yirgacheffe as yg
from snakemake_argparse_bridge import snakemake_compatible

# Buffer distances in metres (half road width) by OSM highway type
WIDTH_MAP = {
    "motorway":     12.0,
    "trunk":         8.0,
    "primary":       6.0,
    "secondary":     5.0,
    "tertiary":      4.0,
    "residential":   3.0,
    "unclassified":  3.0,
    "service":       2.5,
    "track":         2.0,
    "path":          0.75,
    "footway":       0.75,
    "cycleway":      1.0,
    "steps":         1.0,
}
DEFAULT_BUFFER = 2.5

def normalise_highway_tag(value):
    # OSM highway tags can sometimes be a list; take the first element.
    if isinstance(value, list):
        return value[0]
    return value

def fetch_roads(
    template_raster_path: Path,
    output_path: Path,
) -> None:
    with yg.read_raster(template_raster_path) as template:
        template_area = template.area.reproject(yg.MapProjection("EPSG:4326", 0.001, -0.001))
        template_crs = template.map_projection.name

    # (west, south, east, north)
    bbox = [template_area.left, template_area.bottom, template_area.right, template_area.top]

    print("Fetching OSM road features...")
    roads = ox.features_from_bbox(bbox=bbox, tags={"highway": True})
    roads = roads[roads.geometry.type == "LineString"].copy()
    print(f"{len(roads)} road segments fetched")

    roads["highway"] = roads["highway"].apply(normalise_highway_tag)
    roads["buffer_dist"] = roads["highway"].map(WIDTH_MAP).fillna(DEFAULT_BUFFER)

    roads = roads.to_crs(template.map_projection.name)
    roads["geometry"] = roads.apply(
        lambda row: row.geometry.buffer(row.buffer_dist, cap_style="round", join_style="round"),
            axis=1,        )

    road_polygons = gpd.GeoDataFrame(geometry=[roads.union_all()], crs=template.map_projection.name)
    road_polygons.to_file(output_path, driver="GeoJSON")

@snakemake_compatible(mapping={
    "template_path": "input.template",
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
        '--output',
        type=Path,
        help='Path of lake level raster',
        required=True,
        dest='output_path',
    )
    args = parser.parse_args()

    fetch_roads(
        args.template_path,
        args.output_path,
    )

if __name__ == "__main__":
    main()
