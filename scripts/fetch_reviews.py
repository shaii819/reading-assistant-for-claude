#!/usr/bin/env python3
"""Fetch book reviews from Hardcover, Open Library, and Google Books."""

import json
import os
import sys
from pathlib import Path

import httpx

TIMEOUT = 15.0


def _make_result(source: str, query: str, status: str = "ok",
                 reviews: list | None = None,
                 book_info: dict | None = None,
                 error_message: str | None = None) -> dict:
    return {
        "source": source,
        "query": query,
        "status": status,
        "error_message": error_message,
        "book_info": book_info or {},
        "reviews": reviews or [],
    }


def _fetch_hardcover(title: str, isbn: str | None) -> dict:
    api_key = os.environ.get("HARDCOVER_API_KEY")
    if not api_key:
        return _make_result("hardcover", title, status="skipped",
                             error_message="HARDCOVER_API_KEY not set")
    try:
        query_str = isbn if isbn else title
        gql_query = """
        query SearchBooks($query: String!) {
          books(where: {title: {_ilike: $query}}, limit: 5) {
            id
            title
            slug
            ratings_count
            rating
            reviews(limit: 20) {
              id
              review
              rating
              likes_count
            }
          }
        }
        """
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(
                "https://api.hardcover.app/v1/graphql",
                json={"query": gql_query, "variables": {"query": f"%{title}%"}},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
        resp.raise_for_status()
        data = resp.json()
        books = data.get("data", {}).get("books", [])
        reviews = []
        book_info = {}
        if books:
            book = books[0]
            book_info = {
                "title": book.get("title"),
                "rating": book.get("rating"),
                "ratings_count": book.get("ratings_count"),
            }
            for r in book.get("reviews", []):
                if r.get("review"):
                    reviews.append({
                        "text": r["review"],
                        "rating": r.get("rating"),
                        "likes": r.get("likes_count"),
                    })
        return _make_result("hardcover", title, status="ok",
                             reviews=reviews, book_info=book_info)
    except Exception as exc:
        return _make_result("hardcover", title, status="error",
                             error_message=str(exc))


def _fetch_openlibrary(title: str, isbn: str | None) -> dict:
    try:
        params: dict = {"limit": 5, "fields": "key,title,author_name,ratings_average,ratings_count"}
        if isbn:
            params["isbn"] = isbn
        else:
            params["title"] = title
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get("https://openlibrary.org/search.json", params=params)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("docs", [])
        book_info = {}
        reviews = []
        if docs:
            doc = docs[0]
            book_info = {
                "title": doc.get("title"),
                "authors": doc.get("author_name", []),
                "rating": doc.get("ratings_average"),
                "ratings_count": doc.get("ratings_count"),
            }
        return _make_result("openlibrary", title, status="ok",
                             reviews=reviews, book_info=book_info)
    except Exception as exc:
        return _make_result("openlibrary", title, status="error",
                             error_message=str(exc))


def _fetch_googlebooks(title: str, isbn: str | None) -> dict:
    try:
        if isbn:
            q = f"isbn:{isbn}"
        else:
            q = f"intitle:{title}"
        params = {"q": q, "maxResults": 5, "printType": "books"}
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get("https://www.googleapis.com/books/v1/volumes", params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        book_info = {}
        reviews = []
        if items:
            vol = items[0].get("volumeInfo", {})
            book_info = {
                "title": vol.get("title"),
                "authors": vol.get("authors", []),
                "average_rating": vol.get("averageRating"),
                "ratings_count": vol.get("ratingsCount"),
                "description": vol.get("description", "")[:500],
            }
        return _make_result("googlebooks", title, status="ok",
                             reviews=reviews, book_info=book_info)
    except Exception as exc:
        return _make_result("googlebooks", title, status="error",
                             error_message=str(exc))


def fetch_all_reviews(title: str, isbn: str | None, output_dir: str) -> None:
    """Fetch reviews from all sources and write one JSON file per source."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    sources = [
        ("hardcover", _fetch_hardcover),
        ("openlibrary", _fetch_openlibrary),
        ("googlebooks", _fetch_googlebooks),
    ]
    for name, fetcher in sources:
        result = fetcher(title, isbn)
        (out / f"{name}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fetch_reviews.py <title> <output_dir> [isbn]")
        sys.exit(1)
    title = sys.argv[1]
    out_dir = sys.argv[2]
    isbn = sys.argv[3] if len(sys.argv) > 3 else None
    fetch_all_reviews(title, isbn, out_dir)
    print(f"Reviews written to {out_dir}/")
