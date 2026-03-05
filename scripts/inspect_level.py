#!/usr/bin/env python3
import sys
import nbtlib
from pathlib import Path


def print_nbt(data, indent=0):
    """Recursively print NBT data structure"""
    spacing = "  " * indent

    if isinstance(data, nbtlib.tag.Compound):
        for key, value in data.items():
            type_name = type(value).__name__
            if isinstance(value, (nbtlib.tag.Compound, nbtlib.tag.List)):
                print(f"{spacing}{key}: {type_name}")
                print_nbt(value, indent + 1)
            else:
                print(f"{spacing}{key}: {type_name} = {value}")

    elif isinstance(data, nbtlib.tag.List):
        for i, item in enumerate(data):
            type_name = type(item).__name__
            if isinstance(item, (nbtlib.tag.Compound, nbtlib.tag.List)):
                print(f"{spacing}[{i}]: {type_name}")
                print_nbt(item, indent + 1)
            else:
                print(f"{spacing}[{i}]: {type_name} = {item}")

    else:
        print(f"{spacing}{data}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python inspect_level.py <path_to_level.dat>")
        sys.exit(1)

    level_path = Path(sys.argv[1])

    if not level_path.exists():
        print(f"Error: File not found: {level_path}")
        sys.exit(1)

    print(f"Reading: {level_path}\n")

    try:
        level = nbtlib.load(level_path, gzipped=True)
        print_nbt(level)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
