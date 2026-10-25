# Security

This is a finished, low-maintenance portfolio project (no active feature development), reviewed
periodically for Dependabot/CodeQL alerts. This file tracks dependency-security decisions that
aren't obvious from a diff, so they don't need to be re-investigated from scratch every time.

## Accepted risk: GDAL pinned to 3.4.1

`gdal = "3.4.1"` in `pyproject.toml` is an exact pin, not a caret range, because the `gdal` PyPI
package ships no prebuilt wheels — it always compiles its Python bindings against the system's
`libgdal`. This machine's `libgdal30` (Ubuntu 22.04 "jammy", via apt) is 3.4.1, and no Ubuntu
release or PPA (checked `ubuntugis-unstable`) builds past roughly 3.8.4 for this distro. The known
CVEs in this GDAL line are fixed only in 3.13.0/3.13.1, so none of the available upgrade paths
close them without compiling GDAL from source — a maintenance burden this project won't take on.

Mitigating context: this is a local CLI tool that processes self-sourced Landsat imagery and a
locally authored shapefile. There is no network-facing input and no untrusted file ever reaches
GDAL, which narrows the real-world exposure of these CVEs considerably even though the version
number itself stays behind.

The corresponding GitHub Dependabot alerts are dismissed with this same reasoning. If a newer
GDAL ever becomes installable on a supported Ubuntu release without a from-source build, revisit
the pin.

## GDAL's NumPy extension needs a manual rebuild step

`gdal`'s PyPI package only builds its NumPy array extension (`osgeo._gdal_array`) when NumPy is
visible outside of pip's isolated build environment. A plain `poetry install` leaves it missing,
which silently breaks `read_landsat_band(is_normalize=True)` (used by the `color` command). See
the "Install GDAL" step in [README.md](README.md) for the required follow-up command.

## fiona was dropped (2026-10)

`fiona` is gone as a dependency. `geopandas` 1.x defaults to the `pyogrio` I/O engine instead of
fiona, so pinning/maintaining a compatible fiona version is no longer necessary.
