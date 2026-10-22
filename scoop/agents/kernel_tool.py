"""run_kernel: the agent's computations in the user's own analysis environment (scoop/runtime/kernel.py),
and fits_cutout: sky images as FITS in that environment's working directory, for it to measure."""
from __future__ import annotations

import json
import re
from typing import Annotated, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from pydantic import Field

from ..archives.images import PROJECTIONS, fits_params
from .python_tool import code_result, table_inputs
from .tools import tool_error

HEADER_KEYS = ("NAXIS1", "NAXIS2", "CTYPE1", "CTYPE2", "CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2",
               "CDELT1", "CDELT2", "CD1_1", "CD2_2", "BUNIT", "HIPS_ID")


def header_summary(data: bytes) -> dict:
    """The WCS and units of a FITS image, from its primary header (no astropy needed)."""
    header = {}
    for i in range(0, min(len(data), 2880 * 10), 80):
        card = data[i:i + 80].decode("ascii", errors="replace")
        key = card[:8].strip()
        if key == "END":
            break
        if key in HEADER_KEYS and card[8:10] == "= ":
            text = card[10:].strip()
            if text.startswith("'"):  # a string, which may itself contain "/"
                header[key] = text[1:].split("'", 1)[0].strip()
                continue
            value = text.split("/")[0].strip()
            try:
                header[key] = float(value)
            except ValueError:
                header[key] = value
    return header


def build_kernel_tools(kernel, field=None, fetch_fits=None) -> list[BaseTool]:
    """``fetch_fits`` (scoop.archives.images.fits_fetcher) adds fits_cutout."""
    # field: the field, or a function returning the turn's current field (load_field can switch it).
    current_field = field if callable(field) else (lambda: field)

    @tool
    async def run_kernel(
        code: Annotated[str, Field(min_length=1, max_length=50_000)],
        tool_call_id: Annotated[str, InjectedToolCallId],
        tables: Annotated[list[str], Field(max_length=10)] = [],
        restart: bool = False,
    ):
        """Run Python in the user's own analysis environment: a persistent Jupyter
        kernel with their installed packages and their data files. Use it when the
        work needs a package or data run_python does not have, more memory or time, or
        state kept across steps. Check that a package is installed before relying on it.

        Variables persist between calls: load large data once and reuse it. restart=True
        starts a fresh kernel first. Each table named in `tables` becomes a pandas
        DataFrame of that name (and in `tables`). The working directory is a scratch
        directory; write files only there. Read only data paths the user has given or
        that you found by listing directories they named.

        Output: what you print, plus the value of a final expression. The first
        matplotlib figure is shown to you and the user; put panels in one figure.
        Print summaries (shapes, units, statistics), never whole arrays.
        Long computations are interrupted after the time limit; variables are kept.
        """
        inputs = table_inputs(current_field(), tables)
        if isinstance(inputs, str):
            return tool_error(inputs, tool_call_id)
        try:
            if restart:
                await kernel.restart()
            result = await kernel.run(code, inputs)
        except Exception as exc:  # the kernel failing is an outcome
            return tool_error(f"The kernel failed ({type(exc).__name__}: {exc}).", tool_call_id)
        return code_result("run_kernel", code, result, tool_call_id)

    @tool
    async def fits_cutout(
        hips: str,
        ra: float,
        dec: float,
        fov_deg: Annotated[float, Field(gt=0, le=180)],
        tool_call_id: Annotated[str, InjectedToolCallId],
        pixels: Annotated[int, Field(ge=16, le=4000)] = 1000,
        projection: Literal[PROJECTIONS] = "TAN",
    ):
        """Save a square FITS cutout of any image HiPS (CDS hips2fits) into the kernel's
        working directory, with its WCS, for run_kernel to load and measure (e.g. with
        astropy.io.fits and astropy.wcs). hips is a CDS HiPS id such as CDS/P/DSS2/red,
        CDS/P/2MASS/K or a Planck map; survey_inventory (via the data agent) lists those
        covering the field. TAN suits small fields; CAR or ZEA suit wide ones. Pixel values
        are the HiPS's own (check BUNIT); a HiPS is a resampled mosaic, so use the survey's
        own maps for precise photometry. Returns the file path and the header's WCS."""
        try:
            params = fits_params(ra, dec, fov_deg, hips, pixels, projection)
        except ValueError as exc:
            return tool_error(str(exc), tool_call_id)
        try:
            data = await fetch_fits(params)
        except Exception as exc:  # the service failing is an outcome
            return tool_error(f"hips2fits failed ({type(exc).__name__}: {exc}).", tool_call_id)
        name = (f"{re.sub(r'[^A-Za-z0-9.+-]+', '_', hips)}_{ra:.5f}_{dec:+.5f}_{fov_deg:g}deg_"
                f"{pixels}px_{projection}.fits")
        directory = kernel.cwd / "cutouts"
        directory.mkdir(parents=True, exist_ok=True)
        partial = directory / f".{name}.part"
        partial.write_bytes(data)
        partial.replace(directory / name)
        summary = {"path": str(directory / name), "relative_path": f"cutouts/{name}", "bytes": len(data),
                   "header": header_summary(data)}
        return ToolMessage(content=json.dumps(summary), tool_call_id=tool_call_id)

    return [run_kernel] + ([fits_cutout] if fetch_fits is not None else [])


__all__ = ["build_kernel_tools"]
