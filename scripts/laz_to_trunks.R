library(lid
library(sf)
library(terra)

dtm_files <- list.files("/Users/michael/dev/kullbergcraft/data/dem_tiles",
                        pattern = "\\.tif$|\\.img$", full.names = TRUE)
dtm <- vrt(dtm_files)
dtm_ext <- ext(dtm)

laz_dirs <- c("/Users/michael/dev/kullbergcraft/data/laz_files/70_5",
              "/Users/michael/dev/kullbergcraft/data/laz_files/70_6")
laz_files <- unlist(lapply(laz_dirs, list.files,
                           pattern = "\\.laz$|\\.las$",
                           full.names = TRUE))

all_ttops <- list()

for (i in seq_along(laz_files)) {
  f <- laz_files[[i]]
  h <- readLASheader(f)
  n_points <- h$`Number of point records`

  # Check overlap with DTM
  laz_ext <- ext(h$`Min X`, h$`Max X`, h$`Min Y`, h$`Max Y`)
  if (!relate(dtm_ext, laz_ext, "contains")) {
    cat(sprintf("[%d/%d] SKIPPED (partial/no DTM coverage): %s\n",
                i, length(laz_files), basename(f)))
    next
  }

  cat(sprintf("[%d/%d] Processing (%dM points): %s\n",
              i, length(laz_files), round(n_points/1e6), basename(f)))
  t0 <- proc.time()

  tryCatch({
    las <- readLAS(f, select = "xyzr")
    if (is.empty(las)) next
    cat("  Normalising...\n")
    las <- normalize_height(las, dtm)
    cat("  Rasterising...\n")
    chm <- rasterize_canopy(las, res = 0.5, algorithm = pitfree())
    cat("  Detecting trees...\n")
    ttops <- locate_trees(chm, lmf(ws = function(x) x * 0.07 + 2, hmin = 5))
    ttops$source_file <- basename(f)
    elapsed <- (proc.time() - t0)["elapsed"]
    cat(sprintf("  Done in %.1fs, %d trees\n", elapsed, nrow(ttops)))
    all_ttops[[length(all_ttops) + 1]] <- ttops
  }, error = function(e) {
    cat(sprintf("  ERROR: %s\n", e$message))
  })
}

if (length(all_ttops) == 0) {
  cat("No tiles processed\n")
} else {
  all_ttops <- do.call(rbind, all_ttops)
  cat("Total trees detected:", nrow(all_ttops), "\n")
  st_write(all_ttops, "tree_tops_pitfree.gpkg", delete_dsn = TRUE)
}
