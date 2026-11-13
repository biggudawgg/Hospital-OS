"""
mcp_servers/openfda/server.py — openFDA Drug Information MCP Server (custom, small).

Why custom? There is no well-maintained official openFDA MCP server, so we wrap
the free public openFDA API (https://open.fda.gov) ourselves. No API key is needed
(an optional OPENFDA_API_KEY in .env raises the rate limit).

Only public drug information is sent to openFDA (a drug name). Never patient data.

Tools:
  1. drug_label_info(drug_name)           -> [OPERATION: READ]
  2. drug_adverse_events(drug_name, limit) -> [OPERATION: READ]
"""

import json
import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("HospitalOS-openFDA")

BASE_URL = "https://api.fda.gov/drug"
TIMEOUT_SECONDS = 10


def _clean_drug_name(drug_name: str) -> str | None:
    """Return a safe search term (letters, digits, spaces, hyphens) or None if invalid."""
    if not isinstance(drug_name, str):
        return None
    name = drug_name.strip()
    # Drop strengths like "500mg" so "Paracetamol 650mg" searches "Paracetamol"
    words = [w for w in name.split() if not any(ch.isdigit() for ch in w)]
    name = " ".join(words)
    if not name or len(name) > 60 or not all(ch.isalnum() or ch in " -" for ch in name):
        return None
    return name


def _get(endpoint: str, params: dict) -> dict:
    """Call openFDA and return JSON. Raises httpx errors for the caller to turn into friendly text."""
    api_key = os.getenv("OPENFDA_API_KEY")
    if api_key:
        params = {**params, "api_key": api_key}
    response = httpx.get(f"{BASE_URL}/{endpoint}.json", params=params, timeout=TIMEOUT_SECONDS)
    if response.status_code == 404:  # openFDA answers 404 when nothing matches
        return {"results": []}
    response.raise_for_status()
    return response.json()


def _first(value):
    """openFDA fields are lists of strings; return the first one, shortened."""
    if isinstance(value, list) and value:
        text = value[0]
        return text[:600] + ("..." if len(text) > 600 else "")
    return None


@mcp.tool()
def drug_label_info(drug_name: str) -> str:
    """
    [OPERATION: READ]
    Look up official US FDA drug label information for a medicine: purpose,
    indications, warnings, common dosage and the manufacturer.
    Uses the free public openFDA API (needs internet). Sends only the drug name.

    Use this when staff ask things like:
    - "What are the warnings for ibuprofen?"
    - "What is metformin used for?"

    Args:
        drug_name: Generic or brand name, e.g. "ibuprofen", "Metformin 500mg".
    """
    name = _clean_drug_name(drug_name)
    if not name:
        return "Friendly Error: please give a plain drug name, e.g. 'ibuprofen'."
    try:
        query = f'openfda.generic_name:"{name}" OR openfda.brand_name:"{name}"'
        data = _get("label", {"search": query, "limit": 1})
        results = data.get("results", [])
        if not results:
            return f"No FDA label found for '{name}'. It may use a different name in the US."
        label = results[0]
        openfda = label.get("openfda", {})
        return json.dumps({
            "operation": "READ",
            "drug": name,
            "brand_names": openfda.get("brand_name", [])[:3],
            "manufacturer": _first(openfda.get("manufacturer_name")),
            "purpose": _first(label.get("purpose")),
            "indications": _first(label.get("indications_and_usage")),
            "warnings": _first(label.get("warnings") or label.get("boxed_warning")),
            "dosage": _first(label.get("dosage_and_administration")),
            "source": "openFDA drug label API (public data, not medical advice)",
        }, indent=2)
    except httpx.TimeoutException:
        return "Friendly Error: openFDA did not answer in time. Please try again."
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            return "Friendly Error: openFDA rate limit reached. Please wait a minute."
        return f"Friendly Error: openFDA returned HTTP {exc.response.status_code}."
    except httpx.HTTPError:
        return "Friendly Error: could not reach openFDA (no internet connection?)."


@mcp.tool()
def drug_adverse_events(drug_name: str, limit: int = 5) -> str:
    """
    [OPERATION: READ]
    List the most commonly REPORTED adverse reactions (side effects) for a drug,
    counted from the FDA Adverse Event Reporting System via openFDA.
    These are report counts, not proof that the drug caused the reaction.

    Use this when staff ask: "What side effects are reported for amoxicillin?"

    Args:
        drug_name: Generic or brand name, e.g. "amoxicillin".
        limit: How many top reactions to return (1-20, default 5).
    """
    name = _clean_drug_name(drug_name)
    if not name:
        return "Friendly Error: please give a plain drug name, e.g. 'amoxicillin'."
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        return "Friendly Error: limit must be a whole number between 1 and 20."
    try:
        data = _get("event", {
            "search": f'patient.drug.medicinalproduct:"{name}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": limit,
        })
        results = data.get("results", [])
        if not results:
            return f"No adverse event reports found for '{name}'."
        return json.dumps({
            "operation": "READ",
            "drug": name,
            "top_reported_reactions": [{"reaction": r["term"], "reports": r["count"]} for r in results],
            "note": "Counts of reports, not proven side effects. Not medical advice.",
        }, indent=2)
    except httpx.TimeoutException:
        return "Friendly Error: openFDA did not answer in time. Please try again."
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            return "Friendly Error: openFDA rate limit reached. Please wait a minute."
        return f"Friendly Error: openFDA returned HTTP {exc.response.status_code}."
    except httpx.HTTPError:
        return "Friendly Error: could not reach openFDA (no internet connection?)."


if __name__ == "__main__":
    mcp.run()
