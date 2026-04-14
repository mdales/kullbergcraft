library(terra)
library(sf)
library(smoothr)

lc <- rast(snakemake@input[["lcc"]])
method <- snakemake@params[["smooth_method"]]  # e.g. "chaikin"

polys <- as.polygons(lc, dissolve = TRUE) |> st_as_sf()
polys_smooth <- smoothr::smooth(polys, method = method)

template <- disagg(lc, fact = 10)
lc_smooth <- rasterize(vect(polys_smooth), template, field = names(lc))

fill_gaps <- function(r, fallback, w = 3, max_iter = 10) {
  for (i in seq_len(max_iter)) {
    if (global(r, "isNA")[[1]] == 0) break
    r <- focal(r, w = w, fun = "modal", na.policy = "only", na.rm = TRUE)
  }
  cover(r, fallback)
}

lc_naive <- disagg(lc, fact = 10, method = "near")
lc_smooth_filled <- fill_gaps(lc_smooth, lc_naive)

writeRaster(lc_smooth_filled, snakemake@output[["result"]], overwrite = TRUE)
