"""What's here: every dataset covering a field (CDS MOC server), and FITS cutouts for run_kernel."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from scoop.archives import discovery
from scoop.archives.discovery import region_datasets, survey_inventory
from scoop.archives.images import fits_params

try:
    from starlette.testclient import TestClient

    from scoop.agents.kernel_tool import build_kernel_tools, header_summary
    from scoop.server.app import create_app
except ModuleNotFoundError as exc:
    if exc.name.split(".")[0] not in {"starlette", "langchain_core", "langgraph", "pydantic", "httpx"}:
        raise
    HAS_SERVER = False
else:
    HAS_SERVER = True

GAIA = {"ID": "CDS/I/355/gaiadr3", "obs_title": "Gaia DR3 (Gaia Collaboration, 2022)", "dataproduct_type": "catalog",
        "obs_regime": "Optical",
        "hips_service_url": ["http://mirror.example/gaia", "https://hipscat.cds.unistra.fr/HiPSCatService/I/355/gaiadr3/"],
        "nb_rows": "1811709771", "moc_sky_fraction": "1"}
SMALL = {"ID": "CDS/J/ApJ/1/1/table1", "obs_title": "A paper table", "dataproduct_type": "catalog",
         "hips_service_url": "https://hipscat.cds.unistra.fr/HiPSCatService/J/ApJ/1/1/table1",
         "nb_rows": "120", "moc_sky_fraction": "0.0001"}
IMAGE = {"ID": "CDS/P/DSS2/red", "obs_title": "DSS2 red", "dataproduct_type": "image", "obs_regime": ["Optical"],
         "hips_service_url": "https://alasky.cds.unistra.fr/DSS/DSS2Merged", "moc_sky_fraction": "1",
         "hips_pixel_scale": "2.236E-4"}
HTTP_ONLY = {"ID": "XCat/old", "obs_title": "Old", "dataproduct_type": "catalog",
             "hips_service_url": "http://old.example/cat", "moc_sky_fraction": "1"}


class FakeResponse:
    def __init__(self, records):
        self.records = records

    def raise_for_status(self):
        pass

    def json(self):
        return self.records


class RegionDatasetsTests(unittest.TestCase):
    def setUp(self):
        discovery._host_checks.clear()

    def moc(self, up=("hipscat.cds.unistra.fr", "axel.u-strasbg.fr")):
        """A fake requests.get: the MOC server's records, and properties files on the hosts that are up."""
        self.sent, self.probed = [], []

        def get(url, params=None, timeout=None):
            if params is not None:
                self.sent.append(params)
                return FakeResponse([SMALL, IMAGE, HTTP_ONLY, GAIA, {"ID": None}])
            self.probed.append(url)
            if url.split("/")[2] not in up:
                raise TimeoutError("connect timed out")
            return type("Response", (), {"status_code": 200})()

        return get

    REGION = {"ra": 260.05, "dec": 57.92, "radius_deg": 0.5}

    def test_every_dataset_widest_first_with_what_the_map_needs(self):
        found = region_datasets(self.REGION, http=self.moc())["datasets"]
        self.assertEqual([d["id"] for d in found], ["CDS/I/355/gaiadr3", "CDS/P/DSS2/red", "XCat/old",
                                                    "CDS/J/ApJ/1/1/table1"])
        self.assertEqual(found[0], {"id": "CDS/I/355/gaiadr3", "title": "Gaia DR3 (Gaia Collaboration, 2022)",
                                    "regime": "Optical", "type": "catalog", "sky_fraction": 1.0, "rows": 1811709771,
                                    "url": "https://hipscat.cds.unistra.fr/HiPSCatService/I/355/gaiadr3",
                                    "pixel_arcsec": None})
        image = found[1]
        self.assertEqual((image["type"], image["regime"], image["pixel_arcsec"]), ("image", "Optical", 0.805))
        self.assertIsNone(found[2]["url"])  # http only: listed (the data agent can add it), not drawable
        self.assertNotIn("dataproduct_type", self.sent[0])  # every kind, not only catalogues
        self.assertEqual(len(self.probed), 1)  # one check per host, not per catalogue

    def test_an_unreachable_host_is_replaced_by_the_cds_mirror(self):
        found = region_datasets(self.REGION, http=self.moc(up=("axel.u-strasbg.fr",)))["datasets"]
        self.assertEqual([d["url"] for d in found if d["type"] == "catalog" and d["url"]],
                         ["https://axel.u-strasbg.fr/HiPSCatService/I/355/gaiadr3",
                          "https://axel.u-strasbg.fr/HiPSCatService/J/ApJ/1/1/table1"])

    def test_with_neither_host_answering_the_listed_url_is_kept(self):
        found = region_datasets(self.REGION, http=self.moc(up=()))["datasets"]
        self.assertTrue(found[0]["url"].startswith("https://hipscat.cds.unistra.fr/"))

    def test_the_data_agents_inventory_summarizes_the_same_list(self):
        inventory = survey_inventory(self.REGION, http=self.moc())
        self.assertEqual(inventory["total"], 4)
        self.assertEqual(inventory["by_regime"]["Optical"]["by_type"], {"catalog": 1, "image": 1})


class FitsParamsTests(unittest.TestCase):
    def test_any_hips_and_wide_projections(self):
        params = fits_params(10.68, 41.27, 20.0, "CDS/P/PLANCK/R3/HFI857", 2000, "CAR")
        self.assertEqual((params["format"], params["width"], params["projection"]), ("fits", 2000, "CAR"))

    def test_bad_requests_are_refused(self):
        for args in ((400, 0, 1, "CDS/P/DSS2/red"), (1, 0, 0, "CDS/P/DSS2/red"), (1, 0, 1, "DSS2"),
                     (1, 0, 1, "CDS/P/x?y=1"), (1, 0, 1, "CDS/P/DSS2/red", 99999), (1, 0, 1, "CDS/P/DSS2/red", 100, "XYZ")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                fits_params(*args)


def fits_bytes(**cards) -> bytes:
    lines = ["SIMPLE  =                    T", "BITPIX  =                  -32", "NAXIS   =                    2"]
    lines += [f"{k:<8}= {v if not isinstance(v, str) else repr(v)}" for k, v in cards.items()] + ["END"]
    return "".join(line.ljust(80) for line in lines).ljust(2880).encode("ascii")


@unittest.skipUnless(HAS_SERVER, "optional server dependencies absent")
class FitsCutoutToolTests(unittest.TestCase):
    def test_the_cutout_lands_in_the_kernel_directory_with_its_wcs(self):
        data = fits_bytes(NAXIS1=1000, NAXIS2=1000, CTYPE1="RA---CAR", CTYPE2="DEC--CAR", CRVAL1=10.68,
                          CDELT2=0.02, BUNIT="MJy/sr")
        asked = []

        async def fetch(params):
            asked.append(params)
            return data

        with tempfile.TemporaryDirectory() as tmp:
            kernel = type("Kernel", (), {"cwd": Path(tmp)})()
            tools = {t.name: t for t in build_kernel_tools(kernel, None, fetch)}
            message = asyncio.run(tools["fits_cutout"].ainvoke({"type": "tool_call", "name": "fits_cutout", "id": "c1", "args": {
                "hips": "CDS/P/PLANCK/R3/HFI857", "ra": 10.68, "dec": 41.27, "fov_deg": 20, "projection": "CAR"}}))
            result = json.loads(message.content)
            self.assertEqual(Path(result["path"]).read_bytes(), data)
            self.assertTrue(result["relative_path"].startswith("cutouts/CDS_P_PLANCK_R3_HFI857"))
        self.assertEqual(result["header"], {"NAXIS1": 1000.0, "NAXIS2": 1000.0, "CTYPE1": "RA---CAR",
                                            "CTYPE2": "DEC--CAR", "CRVAL1": 10.68, "CDELT2": 0.02, "BUNIT": "MJy/sr"})
        self.assertEqual(asked[0]["hips"], "CDS/P/PLANCK/R3/HFI857")

    def test_bad_ids_and_failures_are_errors_and_the_tool_needs_a_fetcher(self):
        async def down(params):
            raise ConnectionError("timeout")

        kernel = type("Kernel", (), {"cwd": Path(tempfile.gettempdir())})()
        self.assertEqual([t.name for t in build_kernel_tools(kernel)], ["run_kernel"])
        tool = {t.name: t for t in build_kernel_tools(kernel, None, down)}["fits_cutout"]
        for args, text in (({"hips": "nope"}, "not a HiPS id"), ({"hips": "CDS/P/DSS2/red"}, "hips2fits failed")):
            message = asyncio.run(tool.ainvoke({"type": "tool_call", "name": "fits_cutout", "id": "c1",
                                                "args": {"ra": 1.0, "dec": 2.0, "fov_deg": 0.1, **args}}))
            self.assertEqual(message.status, "error")
            self.assertIn(text, message.content)

    def test_header_summary_ignores_other_cards(self):
        self.assertEqual(header_summary(fits_bytes(OBJECT="M31", BUNIT="adu")), {"BUNIT": "adu"})


@unittest.skipUnless(HAS_SERVER, "optional server dependencies absent")
class EndpointTests(unittest.TestCase):
    DATASET = {"id": "CDS/I/355/gaiadr3", "title": "Gaia DR3", "regime": "Optical", "type": "catalog",
               "sky_fraction": 1.0, "rows": 1, "url": "https://x", "pixel_arcsec": None}

    def setUp(self):
        self.calls = []

        async def lister(region):
            self.calls.append(region)
            if region["dec"] < -80:
                raise ConnectionError("MOC server down")
            return {"region": region, "datasets": [self.DATASET] * 400, "source": "test"}

        self.client = TestClient(create_app(list_datasets=lister))

    def test_listed_rounded_cached_and_compressed(self):
        first = self.client.get("/api/datasets?ra=260.0512&dec=57.9154&radius=0.5")
        again = self.client.get("/api/datasets?ra=260.0498&dec=57.9161&radius=0.5")
        self.assertEqual(first.json()["datasets"][0], self.DATASET)
        self.assertEqual(again.json(), first.json())
        self.assertEqual(self.calls, [{"ra": 260.05, "dec": 57.92, "radius_deg": 0.5}])
        self.assertEqual(first.headers["content-encoding"], "gzip")  # a field's list is hundreds of kB

    def test_bad_regions_and_an_outage(self):
        for query in ("", "?ra=1&dec=2", "?ra=400&dec=0&radius=1", "?ra=1&dec=0&radius=90", "?ra=x&dec=0&radius=1"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"/api/datasets{query}").status_code, 400)
        down = self.client.get("/api/datasets?ra=1&dec=-85&radius=1")
        self.assertEqual((down.status_code, down.json()["datasets"]), (502, []))

    def test_off_without_a_lister(self):
        self.assertEqual(TestClient(create_app()).get("/api/datasets?ra=1&dec=2&radius=1").json(), {"datasets": []})


if __name__ == "__main__":
    unittest.main()
