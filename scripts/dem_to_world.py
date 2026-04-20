import argparse
import math
import os
import random
from functools import partial
from pathlib import Path
from sys import platlibdir

from anvil import EmptyRegion, EmptyChunk, Block, Biome
import nbtlib
from anvil.errors import OutOfBoundsCoordinates
from nbtlib import tag
from nbt import nbt
import geopandas as gpd
import numpy as np
from scripts import create_level
from snakemake_argparse_bridge import snakemake_compatible
import yirgacheffe as yg

def create_level_dat(
    output_path: Path,
    level_name: str = "Generated World",
    spawn_x: int = 0,
    spawn_y: int = 64,
    spawn_z: int = 0
) -> None:
    level_data = nbtlib.File({
        'Data': tag.Compound({
            # Version info (1.21.11)
            'Version': tag.Compound({
                'Id': tag.Int(4671),
                'Name': tag.String('1.21.11'),
                'Series': tag.String('main'),
                'Snapshot': tag.Byte(0),
            }),
            'DataVersion': tag.Int(4671),

            # Basic world properties
            'LevelName': tag.String(level_name),
            'version': tag.Int(19133),
            'initialized': tag.Byte(1),
            'WasModded': tag.Byte(0),
            'allowCommands': tag.Byte(1),  # Enable commands

            # Time
            'Time': tag.Long(0),
            'DayTime': tag.Long(0),
            'LastPlayed': tag.Long(0),

            # Difficulty
            'Difficulty': tag.Byte(2),  # Normal
            'DifficultyLocked': tag.Byte(0),
            'hardcore': tag.Byte(0),
            'GameType': tag.Int(1),  # Creative

            # Weather
            'raining': tag.Byte(0),
            'rainTime': tag.Int(0),
            'thundering': tag.Byte(0),
            'thunderTime': tag.Int(0),
            'clearWeatherTime': tag.Int(0),

            # Spawn location
            'spawn': tag.Compound({
                'pos': tag.IntArray([spawn_x, spawn_y, spawn_z]),
                'dimension': tag.String('minecraft:overworld'),
                'yaw': tag.Float(0.0),
                'pitch': tag.Float(0.0),
            }),

            # World generation settings
            'WorldGenSettings': tag.Compound({
                'bonus_chest': tag.Byte(0),
                'generate_features': tag.Byte(1),
                'seed': tag.Long(0),
                'dimensions': tag.Compound({
                    'minecraft:overworld': tag.Compound({
                        'type': tag.String('minecraft:overworld'),
                        'generator': tag.Compound({
                            'type': tag.String('minecraft:noise'),
                            'biome_source': tag.Compound({
                                'type': tag.String('minecraft:multi_noise'),
                                'preset': tag.String('minecraft:overworld'),
                            }),
                            'settings': tag.String('minecraft:overworld'),
                        }),
                    }),
                    'minecraft:the_nether': tag.Compound({
                        'type': tag.String('minecraft:the_nether'),
                        'generator': tag.Compound({
                            'type': tag.String('minecraft:noise'),
                            'biome_source': tag.Compound({
                                'type': tag.String('minecraft:multi_noise'),
                                'preset': tag.String('minecraft:nether'),
                            }),
                            'settings': tag.String('minecraft:nether'),
                        }),
                    }),
                    'minecraft:the_end': tag.Compound({
                        'type': tag.String('minecraft:the_end'),
                        'generator': tag.Compound({
                            'type': tag.String('minecraft:noise'),
                            'biome_source': tag.Compound({
                                'type': tag.String('minecraft:the_end'),
                            }),
                            'settings': tag.String('minecraft:end'),
                        }),
                    }),
                }),
            }),

            # Server brands
            'ServerBrands': tag.List[tag.String]([tag.String('vanilla')]),

            # Wandering trader
            'WanderingTraderSpawnChance': tag.Int(25),
            'WanderingTraderSpawnDelay': tag.Int(24000),

            # Dragon fight
            'DragonFight': tag.Compound({
                'DragonKilled': tag.Byte(0),
                'PreviouslyKilled': tag.Byte(0),
                'NeedsStateScanning': tag.Byte(1),
                'Gateways': tag.List[tag.Int]([]),
            }),

            # Custom boss events
            'CustomBossEvents': tag.Compound({}),

            # Scheduled events
            'ScheduledEvents': tag.List([]),

            # Data packs
            'DataPacks': tag.Compound({
                'Enabled': tag.List[tag.String]([tag.String('vanilla')]),
                'Disabled': tag.List[tag.String]([]),
            }),
        })
    })

    # Save with gzip compression
    level_data.save(str(output_path), gzipped=True)
    print(f"Created level.dat at {output_path}")


def build_nmd_crosswalk():
    return {
        # Null - work in progress marker
        0: Block('minecraft', 'sand'),
        # forest
        1: Block('minecraft', 'grass_block'),
        11: Block('minecraft', 'grass_block'),
        12: Block('minecraft', 'grass_block'),
        111: Block('minecraft', 'grass_block'),
        112: Block('minecraft', 'grass_block'),
        113: Block('minecraft', 'grass_block'),
        114: Block('minecraft', 'grass_block'),
        115: Block('minecraft', 'grass_block'),
        116: Block('minecraft', 'grass_block'),
        117: Block('minecraft', 'grass_block'),
        121: Block('minecraft', 'podzol'),
        122: Block('minecraft', 'podzol'),
        123: Block('minecraft', 'podzol'),
        124: Block('minecraft', 'podzol'),
        125: Block('minecraft', 'podzol'),
        126: Block('minecraft', 'podzol'),
        127: Block('minecraft', 'podzol'),
        118: Block('minecraft', 'grass_block'),
        128: Block('minecraft', 'podzol'),
        # wetland
        2: Block('minecraft', 'podzol'),
        # arable
        3: Block('minecraft', 'dirt'),
        # other open land
        4: Block('minecraft', 'grass_block'),
        41: Block('minecraft', 'grass_block'),
        42: Block('minecraft', 'grass_block'),
        # exploited land
        5: Block('minecraft', 'cobblestone'),
        51: Block('minecraft', 'bricks'),
        52: Block('minecraft', 'dirt'),
        53: Block('minecraft', 'stone'), # road
        # water
        6: Block('minecraft', 'water'),
        61: Block('minecraft', 'water'),
        62: Block('minecraft', 'water'),
    }

def make_tree(log_style: str, leaf_style: str, chunk, height, x, y, z) -> None:
    log = Block('minecraft', log_style)
    leaf = Block('minecraft', leaf_style, {'persistent': 'true'})
    try:
        for i in range(height):
            chunk.set_block(log, x, y + i, z)
        chunk.set_block(leaf, x, y + height, z)
    except OutOfBoundsCoordinates:
        pass

make_tree_pine = partial(make_tree, 'spruce_log', 'spruce_leaves')
make_tree_spruce = partial(make_tree, 'spruce_log', 'spruce_leaves')
make_tree_birch = partial(make_tree, 'birch_log', 'birch_leaves')
make_tree_oak = partial(make_tree, 'oak_log', 'oak_leaves')

def dem_to_world(
    dtm_path: Path,
    dsm_path: Path,
    tree_path: Path,
    lcc_path: Path,
    wires_path: Path,
    cameras_path: Path,
    output_path: Path,
) -> None:
    with (
        yg.read_rasters(dtm_path.glob("*.tif")) as dtm,
        yg.read_raster(dsm_path) as dsm,
        yg.read_raster(lcc_path) as lcc,
        yg.read_raster(tree_path) as trees,
        yg.read_shape_like(wires_path, dsm) as wires,
    ):
        layers = [dtm, dsm, lcc, trees]
        intersection = yg.find_intersection(layers)

        area_dtm   = dtm.as_area(intersection)
        area_dsm   = dsm.as_area(intersection)
        area_trees = trees.as_area(intersection)
        area_lcc   = lcc.as_area(intersection)
        area_wires = wires.as_area(intersection)

        # Create output directory
        os.makedirs(output_path / "region", exist_ok=True)

        create_level_dat(output_path / "level.dat", "kullberg", 1030, 43, 1080)

        min_dem = dtm.min()
        print(min_dem)

        # assert dem.window == lcc.window

        # we can't have more than 255 blocks in height!
        crosswalk = build_nmd_crosswalk()

        # Define some blocks
        bedrock = Block('minecraft', 'bedrock')
        stone = Block('minecraft', 'stone')
        dirt = Block('minecraft', 'dirt')

        # Calculate dimensions
        width, height = dtm.dimensions
        chunks_x = (width + 15) // 16
        chunks_z = (height + 15) // 16

        print(f"Creating world for {width}x{height} terrain ({chunks_x}x{chunks_z} chunks)")

        # Track regions we've created
        regions = {}

        # Process chunk by chunk
        for chunk_x in range(chunks_x):
            for chunk_z in range(chunks_z):
                # Determine which region this chunk belongs to
                region_x = chunk_x // 32
                region_z = chunk_z // 32
                region_key = (region_x, region_z)

                # Create region if we haven't seen it yet
                if region_key not in regions:
                    print(f"Creating region ({region_x}, {region_z})")
                    regions[region_key] = EmptyRegion(region_x, region_z)

                region = regions[region_key]

                # Create the chunk
                chunk = EmptyChunk(chunk_x, chunk_z)

                base_x = chunk_x * 16 #+ 7000
                base_z = chunk_z * 16 #+ 5000

                elev_chunk = area_dtm.read_array(base_x, base_z, 16, 16)
                surf_chunk = area_dsm.read_array(base_x, base_z, 16, 16)
                tree_chunk = area_trees.read_array(base_x, base_z, 16, 16)
                lcc_chunk = area_lcc.read_array(base_x, base_z, 16, 16)
                wires_chunk = area_wires.read_array(base_x, base_z, 16, 16)

                # Fill the chunk with terrain
                for local_x in range(16):
                # if 0:
                    world_x = chunk_x * 16 + local_x #+ 7000
                    if world_x >= width:
                        continue

                    for local_z in range(16):
                        world_z = chunk_z * 16 + local_z #+ 5000
                        if world_z >= height:
                            continue

                        elevation = elev_chunk[local_z, local_x]
                        surface = surf_chunk[local_z, local_x]
                        is_tree = tree_chunk[local_z, local_x] > 0
                        land_type = lcc_chunk[local_z, local_x]
                        is_wire = wires_chunk[local_z, local_x]

                        block_height = min(int(5 + elevation - min_dem), 255)
                        try:
                            tree_height = math.ceil(surface - elevation)
                        except ValueError:
                            tree_height = 0

                        # Place bedrock at bottom
                        chunk.set_block(bedrock, local_x, 0, local_z)

                        try:
                            target = crosswalk[land_type]
                        except KeyError:
                            print(f"{land_type} not in crosswalk")
                            target = Block('minecraft', 'cobblestone')

                        if target.id == 'water':
                            chunk.set_biome(Biome('minecraft', 'frozen_river'), local_x, local_z)
                            for y in range(1, min(block_height, 255)):
                                if y < block_height - 4:
                                    block = stone
                                elif y < block_height - 1:
                                    block = target
                                else:
                                    block = target #Block('minecraft', 'ice')

                                chunk.set_block(block, local_x, y, local_z)
                        else:
                            chunk.set_biome(Biome('minecraft', 'taiga'), local_x, local_z)
                            for y in range(1, min(block_height, 255)):  # Minecraft height limit
                                if y < block_height - 4:
                                    block = stone
                                elif y < block_height - 1:
                                    block = dirt
                                else:
                                    block = target

                                chunk.set_block(block, local_x, y, local_z)

                        if is_tree and not is_wire:
                            if land_type in [2, 42]:
                                make_tree_pine(chunk, tree_height, local_x, block_height, local_z)
                            if land_type in [111, 121]:
                                make_tree_pine(chunk, tree_height, local_x, block_height, local_z)
                            elif land_type in [112, 122]:
                                make_tree_spruce(chunk, tree_height, local_x, block_height, local_z)
                            elif land_type in [113, 123]:
                                make_tree_birch(chunk, tree_height, local_x, block_height, local_z)
                            elif land_type in [114, 115, 116, 116, 124, 125, 126, 127]:
                                x = random.random()
                                if x < 0.3:
                                    make_tree_pine(chunk, tree_height, local_x, block_height, local_z)
                                elif x < 0.6:
                                    make_tree_spruce(chunk, tree_height, local_x, block_height, local_z)
                                else:
                                    make_tree_birch(chunk, tree_height, local_x, block_height, local_z)
                            elif land_type in [41]:
                                plant_choice = random.choice([
                                    Block('minecraft', 'short_grass'),
                                    Block('minecraft', 'fern'),
                                ])
                                try:
                                    chunk.set_block(plant_choice, local_x, block_height + 1, local_z)
                                except OutOfBoundsCoordinates:
                                    pass
                        else:
                            rn = random.random()
                            if rn < 0.3:
                                if land_type in [
                                111, 121, 112, 122, 113, 123, 114, 115, 116, 117, 124, 125, 126, 127,
                                3,
                                ]:
                                    plant_choice = random.choice([
                                        Block('minecraft', 'short_grass'),
                                        Block('minecraft', 'fern'),
                                    ])
                                    try:
                                        chunk.set_block(plant_choice, local_x, block_height, local_z)
                                    except OutOfBoundsCoordinates:
                                        pass
                            elif rn < 0.5:
                                if land_type in [4, 42]:
                                    plant_choice = random.choice([
                                        Block('minecraft', 'short_grass'),
                                        Block('minecraft', 'fern'),
                                    ])
                                    try:
                                        chunk.set_block(plant_choice, local_x, block_height, local_z)
                                    except OutOfBoundsCoordinates:
                                        pass
#
#                         if land_type == 200:
#                             place_beacon(chunk, local_x, y + 1, local_z)
                        # if land_type == 3:
                        #     block = Block('minecraft', 'wheat')
                        #     chunk.set_block(block, local_x, block_height, local_z)

                        if not math.isnan(surface) and tree_height > 1:
                            if land_type == 51:
                                for i in range(tree_height):
                                    chunk.set_block(Block('minecraft', 'bricks'), local_x, block_height + i, local_z)
                                chunk.set_block(stone, local_x, block_height + tree_height, local_z)
                            else:
                                if is_wire:
                                    leaf_type = 'glass'
                                elif tree_height == 1:
                                    leaf_type = random.choice(['short_grass', 'fern'])
                                else:
                                    if land_type in [2, 42]:
                                        leaf_type = 'spruce_leaves'
                                    elif land_type in [111, 121]:
                                        leaf_type = 'spruce_leaves'
                                    elif land_type in [112, 122]:
                                        leaf_type = 'spruce_leaves'
                                    elif land_type in [113, 123]:
                                        leaf_type = 'birch_leaves'
                                    elif land_type in [114, 115, 116, 117, 118, 124, 125, 126, 127, 128]:
                                        x = random.random()
                                        if x < 0.3:
                                            leaf_type = 'spruce_leaves'
                                        elif x < 0.6:
                                            leaf_type = 'spruce_leaves'
                                        else:
                                            leaf_type = 'birch_leaves'
                                    else:
                                        # if we're here, and we lack info, then check the nearby pixels for a forest class
                                        local_lcc = set(np.unique(lcc.read_array(world_x - 10, world_z - 10, 21, 21)))
                                        if set([111, 112, 113, 114, 115, 116, 117, 118, 121, 122, 123, 124, 125, 126, 127, 128]) & local_lcc:
                                            leaf_type = 'spruce_leaves'
                                        else:
                                            leaf_type = 'glass'
                                leaf_block = Block('minecraft', leaf_type, {'persistent': 'true'})
                                try:
                                    chunk.set_block(leaf_block, local_x, block_height + tree_height, local_z)
                                except OutOfBoundsCoordinates:
                                    pass

                # Add chunk to region
                region.add_chunk(chunk)

                # Progress
                # if chunk_x % 32 == 0 and chunk_z == 0:
                progress = chunk_x / chunks_x * 100
                # print(f"  Progress: {progress:.1f}%")

        # Add beacon for cameras
        def set_block(x, y, z, block):
            chunk_x = int(x // 16)
            chunk_z = int(z // 16)
            local_x = int(x - (chunk_x * 16))
            local_z = int(z - (chunk_z * 16))
            region_x = chunk_x // 32
            region_z = chunk_z // 32
            region_key = (region_x, region_z)
            region = regions[region_key]
            chunk = region.get_chunk(chunk_x, chunk_z)
            chunk.set_block(block, local_x, y, local_z)


        pyramid_block = Block('minecraft', 'diamond_block')
        beacon = Block('minecraft', 'beacon')
        cameras = gpd.read_file(cameras_path)
        for point in cameras.geometry:
            print(point)
            x = int((point.x - intersection.left) - 000)
            z = int((intersection.top - point.y) - 000)

            chunk_x = int(x // 16)
            chunk_z = int(z // 16)
            local_x = int(x - (chunk_x * 16))
            local_z = int(z - (chunk_z * 16))
            base_x = chunk_x * 16 + 000
            base_z = chunk_z * 16 + 000
            elev_chunk = area_dtm.read_array(base_x, base_z, 16, 16)
            elevation = elev_chunk[local_z, local_x]
            print(elevation)
            print(min_dem)

            block_height = min(int(5 + elevation - min_dem), 255) - 1
            print(block_height)


            set_block(x, block_height, z, beacon)

            # Set beacon block entity with Levels pre-seeded
            chunk_x = int(x // 16)
            chunk_z = int(z // 16)
            region_key = (chunk_x // 32, chunk_z // 32)
            chunk = regions[region_key].get_chunk(chunk_x, chunk_z)

            beacon_te = nbt.TAG_Compound()
            beacon_te.tags.extend([
                nbt.TAG_String(name='id', value='minecraft:beacon'),
                nbt.TAG_Int(name='x', value=x),
                nbt.TAG_Int(name='y', value=block_height),
                nbt.TAG_Int(name='z', value=z),
                nbt.TAG_Int(name='Levels', value=1),
                nbt.TAG_Compound(name='components'),
            ])
            chunk.add_tile_entity(beacon_te)

            # Place 3x3 base at y-1 (underground)
            for dx in [-1, 0, 1]:
                xpos = x + dx
                for dz in [-1, 0, 1]:
                    zpos = z + dz
                    set_block(xpos, block_height - 1, zpos, pyramid_block)


        # Save all regions
        print("Saving regions...")
        for (region_x, region_z), region in regions.items():
            region.save(str(output_path / f'region/r.{region_x}.{region_z}.mca'))
            print(f"  Saved region ({region_x}, {region_z})")

@snakemake_compatible(mapping={
    "dtm_path": "input.dtm",
    "dsm_path": "input.dsm",
    "tree_path": "input.trees",
    "lcc_path": "input.lcc",
    "wires_path": "input.wires",
    "cameras_path": "input.cameras",
    "output_dir_path": "output[0]",
})
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dtm',
        type=Path,
        help='dtm raster',
        required=True,
        dest='dtm_path',
    )
    parser.add_argument(
        '--dsm',
        type=Path,
        help='dsm raster',
        required=True,
        dest='dsm_path',
    )
    parser.add_argument(
        '--trees',
        type=Path,
        help="Tree points GPKG",
        required=True,
        dest='tree_path',
    )
    parser.add_argument(
        '--lcc',
        type=Path,
        help='LCC raster',
        required=True,
        dest='lcc_path',
    )
    parser.add_argument(
        '--wires',
        type=Path,
        help='clipped wires gpkg',
        required=True,
        dest='wires_path',
    )
    parser.add_argument(
        '--cameras',
        type=Path,
        help='camera locations gpkg',
        required=True,
        dest='cameras_path',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Path of directory for combined rasters raster',
        required=True,
        dest='output_dir_path',
    )
    args = parser.parse_args()
    dem_to_world(
        args.dtm_path,
        args.dsm_path,
        args.tree_path,
        args.lcc_path,
        args.wires_path,
        args.cameras_path,
        args.output_dir_path,
    )


if __name__ == "__main__":
    main()
