"""The exoplanet agent's paper lookups go through SCOOP's ADS client, and what they find
reaches the Literature panel; the claim checks still read the same JSON."""
import asyncio
import json
import unittest

try:
    import httpx
    from langchain_core.messages import AIMessage

    from scoop.agents.exoplanet_agent import build_exoplanet_tool
    from scoop.exoplanets.agent import ask
    from scoop.exoplanets.tools import paper_tools
    from scoop.literature.ads import ADSClient
except ModuleNotFoundError as exc:
    if exc.name.split(".")[0] not in {"langgraph", "langchain_core", "pydantic", "httpx"}:
        raise
    raise unittest.SkipTest("optional chat dependencies absent")

BIBCODE = "2025ApJ...995L..39T"
ABSTRACT = "We find the dayside of TOI-561 b is inconsistent with a bare rock<BR /> (R<SUB>p</SUB> &amp; T)."
DOC = {"bibcode": BIBCODE, "title": ["A thick atmosphere on TOI-561 b"], "author": ["Teske, J.", "Other, A."],
       "abstract": ABSTRACT, "year": "2025", "pub": "The Astrophysical Journal", "doctype": "article",
       "citation_count": 12}


def ads_client(status=200, docs=(DOC,), sent=None):
    def respond(request):
        if sent is not None:
            sent.append(request)
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, json={"response": {"numFound": len(docs), "docs": list(docs)}})

    http = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    return ADSClient("fixture-token", client=http), http


def invoke(tool, args, call_id="c1"):
    return asyncio.run(tool.ainvoke({"type": "tool_call", "name": tool.name, "id": call_id, "args": args}))


class Model:
    """Scripted: fetch the abstract, then answer quoting it."""

    def __init__(self, *turns):
        self.turns = iter(turns)

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages, config=None):
        turn = next(self.turns)
        if isinstance(turn, str):
            return AIMessage(content=turn)
        return AIMessage(content="", tool_calls=[{**turn, "type": "tool_call"}])


ANSWER = json.dumps({"claims": [{"text": "The dayside is inconsistent with a bare rock.", "source": BIBCODE,
                                 "quote": "the dayside of TOI-561 b is inconsistent with a bare rock"}]})


class PaperToolTests(unittest.TestCase):
    def test_search_and_abstract_use_the_client_and_carry_its_payload(self):
        sent = []
        ads, http = ads_client(sent=sent)
        tools = {t.name: t for t in paper_tools(ads)}
        found = invoke(tools["find_papers"], {"query": '"TOI-561 b" atmosphere', "refereed_only": True})
        abstract = invoke(tools["get_abstract"], {"bibcode": BIBCODE})
        asyncio.run(http.aclose())

        papers = json.loads(found.content)
        self.assertEqual(papers["papers"][0]["bibcode"], BIBCODE)
        self.assertEqual((papers["papers"][0]["type"], papers["n_found"]), ("article", 1))
        self.assertIn(("fq", "property:refereed"), list(sent[0].url.params.multi_items()))
        self.assertEqual(sent[0].headers["Authorization"], "Bearer fixture-token")
        # The model and the quote check read plain text; the panel gets the client's payload.
        self.assertEqual(json.loads(abstract.content)["abstract"],
                         "We find the dayside of TOI-561 b is inconsistent with a bare rock (Rp & T).")
        for message in (found, abstract):
            self.assertEqual(message.artifact["service"], "ADS")
            self.assertEqual(message.artifact["papers"][0]["ref"]["native_id"], BIBCODE)

    def test_without_ads_or_with_ads_down_the_model_is_told_to_say_so(self):
        ads, http = ads_client(status=500)
        for client, text in ((None, "ADS is not configured"), (ads, "ADS request failed (http, HTTP 500)")):
            with self.subTest(text=text):
                message = invoke({t.name: t for t in paper_tools(client)}["get_abstract"], {"bibcode": BIBCODE})
                self.assertEqual(message.status, "error")
                self.assertIn(text, message.content)
                self.assertIn("rather than citing papers from memory", message.content)
        asyncio.run(http.aclose())


class HandOffTests(unittest.TestCase):
    def test_the_agent_checks_quotes_from_the_shared_client(self):
        ads, http = ads_client()
        model = Model({"name": "get_abstract", "args": {"bibcode": BIBCODE}, "id": "a1"}, ANSWER)
        answer = asyncio.run(ask("Does TOI-561 b have an atmosphere?", model, ads=ads))
        asyncio.run(http.aclose())
        self.assertTrue(answer.checked, answer.report.summary())

    def test_papers_reach_the_literature_panel_and_failures_the_audit_log(self):
        ads, http = ads_client()
        model = Model({"name": "get_planets", "args": {"hostname": ""}, "id": "p1"},
                      {"name": "get_abstract", "args": {"bibcode": BIBCODE}, "id": "a1"}, ANSWER)
        tool = build_exoplanet_tool(field=None, model=model, ads=ads)
        command = invoke(tool, {"question": "Does TOI-561 b have an atmosphere?"}, call_id="h1")
        asyncio.run(http.aclose())

        artifacts = command.update["artifacts"]
        self.assertEqual(artifacts["a1"]["service"], "ADS")  # shown in the Literature panel
        self.assertEqual(artifacts["h1"]["kind"], "exoplanet_answer")
        failed = command.update["messages"][0].artifact["inner_failures"]
        self.assertEqual([f["tool"] for f in failed], ["get_planets"])  # the empty hostname


if __name__ == "__main__":
    unittest.main()
