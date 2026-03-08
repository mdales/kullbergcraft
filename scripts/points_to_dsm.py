import laspy
import numpy as np
import glob

laz_files = glob.glob("data/bed0afdb-1327-44af-bb2f-b17487a59960/70_5/*.laz") + glob.glob("data/bed0afdb-1327-44af-bb2f-b17487a59960/70_6/*.laz")

# First pass: find overall bounds
min_x, max_x = np.inf, -np.inf
min_y, max_y = np.inf, -np.inf

for path in laz_files:
    las = laspy.read(path)
    min_x = min(min_x, las.x.min())
    max_x = max(max_x, las.x.max())
    min_y = min(min_y, las.y.min())
    max_y = max(max_y, las.y.max())

RESOLUTION = 1.0
left = np.floor(min_x)
top = np.ceil(max_y)
NCOLS = int(np.ceil((max_x - left) / RESOLUTION))
NROWS = int(np.ceil((top - min_y) / RESOLUTION))

print(f"Grid: {NCOLS} x {NROWS}, origin ({left}, {top})")

# Second pass: rasterise
grid = np.full((NROWS, NCOLS), -np.inf)

for path in laz_files:
    print(f"Processing {path}...")
    las = laspy.read(path)

    mask = np.isin(las.classification, [1, 2])
    x = las.x[mask]
    y = las.y[mask]
    z = las.z[mask]

    col = ((x - left) / RESOLUTION).astype(int)
    row = ((top - y) / RESOLUTION).astype(int)

    valid = (col >= 0) & (col < NCOLS) & (row >= 0) & (row < NROWS)
    np.maximum.at(grid.ravel(), (row[valid] * NCOLS + col[valid]), z[valid])

grid[grid == -np.inf] = np.nan

# Save via Yirgacheffe
import yirgacheffe as yg
r = yg.from_array(grid, (left, top), yg.MapProjection("EPSG:3006", 1.0, -1.0))
r.to_geotiff("data/DSM.tif")