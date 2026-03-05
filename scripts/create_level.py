#!/usr/bin/env python3
import nbtlib
from nbtlib import tag
from pathlib import Path


def create_level_dat(output_path: Path, level_name: str = "Generated World",
                     spawn_x: int = 0, spawn_y: int = 64, spawn_z: int = 0):
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_level.py <output_path> [level_name] [spawn_x] [spawn_y] [spawn_z]")
        print("Example: python create_level.py kullberg_dem/level.dat 'Kullberg DEM' 7500 150 7500")
        sys.exit(1)

    output = Path(sys.argv[1])
    name = sys.argv[2] if len(sys.argv) > 2 else "Generated World"
    spawn_x = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    spawn_y = int(sys.argv[4]) if len(sys.argv) > 4 else 64
    spawn_z = int(sys.argv[5]) if len(sys.argv) > 5 else 0

    create_level_dat(output, name, spawn_x, spawn_y, spawn_z)
