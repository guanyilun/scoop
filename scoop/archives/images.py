"""Sky cutouts from CDS hips2fits: JPEGs for the agent to look at, FITS for analysis.

JPEGs come from the HiPS surveys the map shows, at any position and field of view;
the agent sees the image (it is attached to the conversation after the tool result),
and catalogs remain the source for identifications and numbers. FITS cutouts can be
of any image HiPS (e.g. one survey_inventory lists), with a WCS, for code to measure.
"""
from __future__ import annotations

import base64
import math
import re

HIPS2FITS = "https://alasky.cds.unistra.fr/hips-image-services/hips2fits"
# Surveys the agent may request (the map's backgrounds; checked against hips2fits).
SURVEYS = {
    "CDS/P/DSS2/color": "DSS2 optical color",
    "CDS/P/PanSTARRS/DR1/color-z-zg-g": "Pan-STARRS DR1 optical color",
    "CDS/P/DESI-Legacy-Surveys/DR10/color": "DESI Legacy Surveys DR10 color (deep optical)",
    "CDS/P/SDSS9/color": "SDSS9 optical color",
    "CDS/P/2MASS/color": "2MASS near-infrared color (JHK)",
    "CDS/P/unWISE/color-W2-W1W2-W1": "unWISE mid-infrared color (W1/W2)",
    "CDS/P/PLANCK/R3/HFI/color": "Planck R3 HFI color, 353/545/857 GHz (dust; ~5′ beam)",
    "CDS/P/PLANCK/R3/CMB": "Planck R3 CMB (component-separated; ~5′ beam)",
    # CDS quick-look copies of ACT products, resampled to HiPS; skill surveys/act has the official maps.
    "CDS/P/ACT-PLANCK/DR4DR6/f150": "ACT DR4+DR6 and Planck 150 GHz coadd (CMB, SZ decrements, radio sources; "
                                    "~1.4′ beam; CDS quick-look)",
    "CDS/P/ACT/Planck/DR6/Compton-y": "ACT DR6 and Planck Compton-y (thermal SZ; the Coulton+ 2023 map, not the "
                                      "DR6.02 NILC maps; CDS quick-look)",
}
# The map's background choices: SURVEYS with short names, in this order.
BACKGROUNDS = [
    ("CDS/P/DSS2/color", "DSS2 color"),
    ("CDS/P/PanSTARRS/DR1/color-z-zg-g", "Pan-STARRS DR1 color"),
    ("CDS/P/DESI-Legacy-Surveys/DR10/color", "DESI Legacy Surveys DR10 color"),
    ("CDS/P/SDSS9/color", "SDSS9 color"),
    ("CDS/P/2MASS/color", "2MASS color (JHK)"),
    ("CDS/P/unWISE/color-W2-W1W2-W1", "unWISE color (W1/W2)"),
    ("CDS/P/PLANCK/R3/HFI/color", "Planck HFI color (353–857 GHz)"),
    ("CDS/P/PLANCK/R3/CMB", "Planck R3 CMB"),
    ("CDS/P/ACT-PLANCK/DR4DR6/f150", "ACT+Planck f150 (DR4+DR6, quick-look)"),
    ("CDS/P/ACT/Planck/DR6/Compton-y", "ACT+Planck Compton-y (Coulton+ 2023, quick-look)"),
]
SIZE = 512  # pixels; enough detail for morphology, small enough to keep cost down
# FITS cutouts: any image HiPS by its CDS id (e.g. CDS/P/DSS2/red, CDS/P/PLANCK/R3/HFI857).
HIPS_ID = re.compile(r"[A-Za-z0-9_.+-]{1,64}(/[A-Za-z0-9_.+-]{1,64}){1,8}")
PROJECTIONS = ("TAN", "SIN", "CAR", "ZEA", "AIT", "MOL")  # CAR suits wide fields and CMB-style maps
MAX_PIXELS = 4000  # per side; ~64 MB of float32 at most


def cutout_params(ra: float, dec: float, fov_deg: float, survey: str) -> dict:
    """Validated query parameters for one JPEG cutout."""
    numbers = (ra, dec, fov_deg)
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in numbers):
        raise ValueError("ra, dec and fov must be finite numbers")
    if not (0 <= ra < 360 and -90 <= dec <= 90):
        raise ValueError("ra must be in [0, 360) and dec in [-90, 90] degrees")
    if not (1 / 3600 <= fov_deg <= 10):
        raise ValueError("fov must be between 1 arcsec and 10 degrees")
    if survey not in SURVEYS:
        raise ValueError(f"unknown survey {survey!r}; choose one of {sorted(SURVEYS)}")
    return {"hips": survey, "width": SIZE, "height": SIZE, "projection": "TAN", "fov": fov_deg,
            "ra": ra, "dec": dec, "format": "jpg"}


def fits_params(ra: float, dec: float, fov_deg: float, hips: str, pixels: int = 1000,
                projection: str = "TAN") -> dict:
    """Validated query parameters for one square FITS cutout."""
    numbers = (ra, dec, fov_deg)
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in numbers):
        raise ValueError("ra, dec and fov must be finite numbers")
    if not (0 <= ra < 360 and -90 <= dec <= 90):
        raise ValueError("ra must be in [0, 360) and dec in [-90, 90] degrees")
    if not (1 / 3600 <= fov_deg <= 180):
        raise ValueError("fov must be between 1 arcsec and 180 degrees")
    if not (isinstance(hips, str) and HIPS_ID.fullmatch(hips)):
        raise ValueError(f"not a HiPS id: {hips!r} (e.g. CDS/P/DSS2/red)")
    if not (isinstance(pixels, int) and 16 <= pixels <= MAX_PIXELS):
        raise ValueError(f"pixels must be between 16 and {MAX_PIXELS}")
    if projection not in PROJECTIONS:
        raise ValueError(f"projection must be one of {list(PROJECTIONS)}")
    return {"hips": hips, "width": pixels, "height": pixels, "projection": projection, "fov": fov_deg,
            "ra": ra, "dec": dec, "format": "fits"}


def fits_fetcher(client):
    """An async ``(params from fits_params) -> FITS bytes`` using an active httpx client."""

    async def fetch(params: dict) -> bytes:
        response = await client.get(HIPS2FITS, params=params, timeout=180.0)
        if response.status_code >= 400:  # e.g. {"title": "Unknown HiPS", "description": "..."}
            try:
                detail = response.json().get("description") or response.json().get("title")
            except ValueError:
                detail = response.text[:200]
            raise ValueError(f"hips2fits refused the request ({response.status_code}): {detail}")
        if not response.content.startswith(b"SIMPLE"):
            raise ValueError("hips2fits did not return a FITS file: " + response.text[:200])
        return response.content

    return fetch


def cutout_fetcher(client):
    """An async ``(ra, dec, fov_deg, survey) -> JPEG bytes`` using an active httpx client."""

    async def fetch(ra: float, dec: float, fov_deg: float, survey: str) -> bytes:
        response = await client.get(HIPS2FITS, params=cutout_params(ra, dec, fov_deg, survey), timeout=60.0)
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/"):
            raise ValueError("hips2fits did not return an image")
        return response.content

    return fetch


def data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")


__all__ = ["BACKGROUNDS", "HIPS2FITS", "PROJECTIONS", "SURVEYS", "cutout_fetcher", "cutout_params", "data_url", "fits_fetcher",
           "fits_params"]
