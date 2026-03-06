import argparse
import os
import random
from pathlib import Path
from sys import platlibdir

from anvil import EmptyRegion, EmptyChunk, Block, Biome
import nbtlib
from nbtlib import tag
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
        3: Block('minecraft', 'grass_block'),
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

def make_tree_pine(chunk, x, y, z) -> None:
    log = Block('minecraft', 'spruce_log')
    leaf = Block('minecraft', 'spruce_leaves', {'persistent': 'true'})
    height = 5 + int(random.random() * 10)
    for i in range(height):
        chunk.set_block(log, x, y + i, z)
    chunk.set_block(leaf, x, y + height, z)

def make_tree_spruce(chunk, x, y, z) -> None:
    log = Block('minecraft', 'spruce_log')
    leaf = Block('minecraft', 'spruce_leaves', {'persistent': 'true'})
    height = 5 + int(random.random() * 5)
    for i in range(height):
        chunk.set_block(log, x, y + i, z)
    chunk.set_block(leaf, x, y + height, z)

def make_tree_birch(chunk, x, y, z) -> None:
    log = Block('minecraft', 'birch_log')
    leaf = Block('minecraft', 'birch_leaves', {'persistent': 'true'})
    height = 5 + int(random.random() * 5)
    for i in range(height):
        chunk.set_block(log, x, y + i, z)
    chunk.set_block(leaf, x, y + height, z)

def place_beacon(chunk, x, y, z):
    """
    Place a beacon with a 3x3 iron block pyramid base.

    Args:
        chunk: anvil chunk object
        x: x coordinate within chunk (0-15)
        y: y coordinate (beacon will be placed here, base at y-1)
        z: z coordinate within chunk (0-15)
    """
    # Create blocks
    iron_block = Block('minecraft', 'iron_block')
    beacon = Block('minecraft', 'beacon')

    # Place 3x3 base at y-1 (underground)
    for dx in [-1, 0, 1]:
        xpos = x + dx
        if xpos < 0 or xpos > 15:
            continue
        for dz in [-1, 0, 1]:
            zpos = z + dz
            if zpos < 0 or zpos > 15:
                continue
            chunk.set_block(iron_block, xpos, y - 1, zpos)

    # Place beacon on top (visible at ground level)
    chunk.set_block(beacon, x, y, z)

def dem_to_world(
    dem_path: Path,
    lcc_path: Path,
    output_path: Path,
) -> None:
    with (
        yg.read_rasters(dem_path.glob("*.tif")) as dem,
        yg.read_raster(lcc_path) as lcc,
    ):
        layers = [dem, lcc]
        intersection = yg.YirgacheffeLayer.find_intersection(layers)
        for layer in layers:
            layer.set_window_for_intersection(intersection)

        # Create output directory
        os.makedirs(output_path / "region", exist_ok=True)

        create_level_dat(output_path / "level.dat", "kullberg", 0, 200, 0)

        min_dem = dem.min()
        max_dem = dem.max()

        # assert dem.window == lcc.window

        # we can't have more than 255 blocks in height!
        crosswalk = build_nmd_crosswalk()

        # Define some blocks
        bedrock = Block('minecraft', 'bedrock')
        stone = Block('minecraft', 'stone')
        dirt = Block('minecraft', 'dirt')

        # Calculate dimensions
        width = dem.window.xsize
        height = dem.window.ysize
        chunks_x = (width + 15) // 16
        chunks_z = (height + 15) // 16

        print(f"Creating world for {width}x{height} terrain ({chunks_x}x{chunks_z} chunks)")

        # Track regions we've created
        regions = {}

        # Process chunk by chunk
        for chunk_x in range(80):
            for chunk_z in range(80):
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

                # Fill the chunk with terrain
                for local_x in range(16):
                    world_x = chunk_x * 16 + local_x + 7500
                    if world_x >= width:
                        continue

                    for local_z in range(16):
                        world_z = chunk_z * 16 + local_z + 5500
                        if world_z >= height:
                            continue

                        elevation = dem.read_array(world_x, world_z, 1, 1)[0][0]
                        block_height = min(int(5 + elevation - min_dem), 255)

                        land_type = lcc.read_array(world_x, world_z, 1, 1)[0][0]

                        # Place bedrock at bottom
                        chunk.set_block(bedrock, local_x, 0, local_z)

                        try:
                            target = crosswalk[land_type]
                        except KeyError:
                            print(f"{land_type} not in crosswalk")
                            target = Block('minecraft', 'cobblestone')


                        # Fill from bedrock to surface
                        if target.id == 'water':
                            chunk.set_biome(Biome('minecraft', 'frozen_river'), local_x, local_z)
                            for y in range(1, min(block_height, 320)):
                                if y < block_height - 4:
                                    block = stone
                                elif y < block_height - 1:
                                    block = target
                                else:
                                    block = target #Block('minecraft', 'ice')

                                chunk.set_block(block, local_x, y, local_z)
                        else:
                            chunk.set_biome(Biome('minecraft', 'snowy_taiga'), local_x, local_z)
                            for y in range(1, min(block_height, 320)):  # Minecraft height limit
                                if y < block_height - 4:
                                    block = stone
                                elif y < block_height - 1:
                                    block = dirt
                                else:
                                    block = target

                                chunk.set_block(block, local_x, y, local_z)

                        rn = random.random()
                        if rn < 0.1:
                            if land_type in [111, 121]:
                                make_tree_pine(chunk, local_x, y, local_z)
                            elif land_type in [112, 122]:
                                make_tree_spruce(chunk, local_x, y, local_z)
                            elif land_type in [113, 123]:
                                make_tree_birch(chunk, local_x, y, local_z)
                            elif land_type in [114, 115, 116, 116, 124, 125, 126, 127]:
                                x = random.random()
                                if x < 0.3:
                                    make_tree_pine(chunk, local_x, y, local_z)
                                elif x < 0.6:
                                    make_tree_spruce(chunk, local_x, y, local_z)
                                else:
                                    make_tree_birch(chunk, local_x, y, local_z)
                            elif land_type in [41]:
                                plant_choice = random.choice([
                                    Block('minecraft', 'short_grass'),
                                    Block('minecraft', 'fern'),
                                ])
                                chunk.set_block(plant_choice, local_x, y + 1, local_z)
                        elif rn < 0.3:
                            if land_type in [
                              111, 121, 112, 122, 113, 123, 114, 115, 116, 116, 124, 125, 126, 127,
                              3,
                            ]:
                                plant_choice = random.choice([
                                    Block('minecraft', 'short_grass'),
                                    Block('minecraft', 'fern'),
                                ])
                                chunk.set_block(plant_choice, local_x, y + 1, local_z)
                        elif rn < 0.5:
                            if land_type in [4, 42]:
                                plant_choice = random.choice([
                                    Block('minecraft', 'short_grass'),
                                    Block('minecraft', 'fern'),
                                ])
                                chunk.set_block(plant_choice, local_x, y + 1, local_z)

                        if land_type == 200:
                            place_beacon(chunk, local_x, y + 1, local_z)

                # Add chunk to region
                region.add_chunk(chunk)

                # Progress
                if chunk_x % 32 == 0 and chunk_z == 0:
                    progress = chunk_x / chunks_x * 100
                    print(f"  Progress: {progress:.1f}%")

        # Save all regions
        print("Saving regions...")
        for (region_x, region_z), region in regions.items():
            region.save(str(output_path / f'region/r.{region_x}.{region_z}.mca'))
            print(f"  Saved region ({region_x}, {region_z})")

@snakemake_compatible(mapping={
    "dem_path": "input.dem",
    "lcc_path": "input.lcc",
    "output_dir_path": "output[0]",
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
        help='Path of directory for combined rasters raster',
        required=True,
        dest='output_dir_path',
    )
    args = parser.parse_args()
    dem_to_world(
        args.dem_path,
        args.lcc_path,
        args.output_dir_path,
    )


if __name__ == "__main__":
    main()
