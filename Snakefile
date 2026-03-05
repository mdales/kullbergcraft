rule find_dem_tiles:
    output:
        "data/stac_search_results.json"
    script:
        "scripts/query_lantmateriet_stac.py"

checkpoint download_dem_tiles:
    input:
        "data/stac_search_results.json"
    output:
        "data/dem_tiles/"
    script:
        "scripts/download_stac_tiles.py"

def get_dem_tiles(wildcards):
    checkpoints.download_dem_tiles.get(**wildcards)
    return expand(
        "data/stripped_dem_tiles/{tile}.tif",
        tile=glob_wildcards("data/dem_tiles/{tile}.tif").tile
    )

rule stripped_tiles:
    input:
        get_dem_tiles

rule remove_vert_projection:
    input:
        "data/dem_tiles/{tile}.tif"
    output:
        "data/stripped_dem_tiles/{tile}.tif"
    shell:
        "gdal_translate -a_srs EPSG:3006 {input} {output}"

rule align_nmd_with_dem:
    input:
        dem="data/stripped_dem_tiles",
        lcc="data/NMD2018_basskikt_ogeneraliserad_Sverige_v1_1/nmd2018bas_ogeneraliserad_v1_1.tif",
    output:
        "data/kullberg_nmd_1m.tif"
    script:
        "scripts/align_nmd_with_dem.py"

rule find_lakes:
    input:
        dem="data/stripped_dem_tiles",
        lcc="data/kullberg_nmd_1m.tif"
    output:
        "data/lakes_1m.tif"
    script:
        "scripts/find_lakes.py"

rule make_land:
    input:
        dem="data/stripped_dem_tiles",
        lcc="data/kullberg_nmd_10m.tif"
    output:
        "data/natural_nmd_1m.tif"
    script:
        "scripts/make_land.py"

rule make_refined_nmd:
    input:
        dem="data/stripped_dem_tiles",
        lcc="data/natural_nmd_1m.tif",
        lakes="data/lakes_1m.tif",
        cameras="data/cameras.gpkg",
    output:
        "data/refined_nmd_1m.tif"
    script:
        "scripts/refined_nmd_1m.py"

rule make_world:
    input:
        dem="data/stripped_dem_tiles",
        lcc="data/refined_nmd_1m.tif",
    output:
        directory("data/kullberg_world")
    script:
        "scripts/dem_to_world.py"
