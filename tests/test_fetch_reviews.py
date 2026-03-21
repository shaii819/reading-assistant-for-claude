import json
from pathlib import Path
import sys

import httpx
import pytest
import respx

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_reviews import fetch_all_reviews


@respx.mock
def test_fetch_writes_per_source_files(tmp_path):
    respx.route(host="api.hardcover.app").mock(
        return_value=httpx.Response(200, json={"data": {"books": []}})
    )
    respx.route(host="openlibrary.org").mock(
        return_value=httpx.Response(200, json={"docs": []})
    )
    respx.route(host="www.googleapis.com").mock(
        return_value=httpx.Response(200, json={"totalItems": 0})
    )

    reviews_dir = tmp_path / "reviews" / "raw"
    fetch_all_reviews("The Art of Testing", None, str(reviews_dir))

    assert (reviews_dir / "hardcover.json").exists()
    assert (reviews_dir / "openlibrary.json").exists()
    assert (reviews_dir / "googlebooks.json").exists()


@respx.mock
def test_fetch_graceful_on_api_error(tmp_path):
    respx.route(host="api.hardcover.app").mock(
        return_value=httpx.Response(500)
    )
    respx.route(host="openlibrary.org").mock(
        return_value=httpx.Response(200, json={"docs": []})
    )
    respx.route(host="www.googleapis.com").mock(
        return_value=httpx.Response(200, json={"totalItems": 0})
    )

    reviews_dir = tmp_path / "reviews" / "raw"
    fetch_all_reviews("Test Book", None, str(reviews_dir))

    hc = json.loads((reviews_dir / "hardcover.json").read_text())
    assert hc["status"] in ("error", "skipped")


@respx.mock
def test_fetch_schema_compliance(tmp_path):
    respx.route(host="api.hardcover.app").mock(
        return_value=httpx.Response(200, json={"data": {"books": []}})
    )
    respx.route(host="openlibrary.org").mock(
        return_value=httpx.Response(200, json={"docs": []})
    )
    respx.route(host="www.googleapis.com").mock(
        return_value=httpx.Response(200, json={"totalItems": 0})
    )

    reviews_dir = tmp_path / "reviews" / "raw"
    fetch_all_reviews("Test", None, str(reviews_dir))

    for fname in ["hardcover.json", "openlibrary.json", "googlebooks.json"]:
        data = json.loads((reviews_dir / fname).read_text())
        assert "source" in data
        assert "query" in data
        assert "status" in data
        assert "reviews" in data
        assert isinstance(data["reviews"], list)
