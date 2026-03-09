from __future__ import annotations

from adk_agent.skills.web_search.tools.web_search import (
    BraveSearchClient,
    DuckDuckGoSearchClient,
    _parse_brave_results,
    _query_variants,
    debug_search_attempts,
)


def test_parse_brave_results_from_json():
    payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "OpenAI launches feature",
            "url": "https://example.com/a",
            "description": "OpenAI announced a new feature this week."
          },
          {
            "title": "Second result",
            "url": "https://example.com/b",
            "description": "Another snippet with 42 percent growth."
          }
        ]
      }
    }
    """

    results = _parse_brave_results(payload, max_results=5)

    assert len(results) == 2
    assert results[0]["href"] == "https://example.com/a"
    assert "OpenAI launches feature" in results[0]["title"]
    assert "new feature" in results[0]["body"]


def test_parse_brave_results_deduplicates_urls():
    payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "Atlanta weather",
            "url": "https://example.com/weather",
            "description": "Current conditions for Atlanta."
          },
          {
            "title": "Atlanta weather duplicate",
            "url": "https://example.com/weather",
            "description": "Duplicate row."
          }
        ]
      }
    }
    """

    results = _parse_brave_results(payload, max_results=5)

    assert len(results) == 1
    assert results[0]["href"] == "https://example.com/weather"
    assert results[0]["title"] == "Atlanta weather"


def test_brave_search_client_shapes_results(monkeypatch):
    payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "OpenAI news",
            "url": "https://example.com/openai",
            "description": "OpenAI grew revenue to 123.4 this year."
          }
        ]
      }
    }
    """

    monkeypatch.setattr(
        "adk_agent.skills.web_search.tools.web_search._fetch_brave_response",
        lambda query, max_results, verify: payload,
    )

    result = BraveSearchClient().search("OpenAI news", max_results=3)

    assert result.answer_text.startswith("Search results:")
    assert result.citations == [{"title": "OpenAI news", "url": "https://example.com/openai"}]
    assert result.snippets == ["OpenAI grew revenue to 123.4 this year."]
    assert 123.4 in result.numbers


def test_duckduckgo_client_alias_points_to_brave():
    assert DuckDuckGoSearchClient is BraveSearchClient


def test_verbose_queries_retry_with_fallback_variants(monkeypatch):
    empty_payload = b'{"web":{"results":[]}}'
    weather_payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "Atlanta weather",
            "url": "https://example.com/atlanta-weather",
            "description": "Current conditions and hourly forecast for Atlanta."
          }
        ]
      }
    }
    """
    seen_queries: list[str] = []

    def _fake_fetch(query: str, max_results: int, verify: bool) -> bytes:
        del max_results, verify
        seen_queries.append(query)
        if query.lower() == "weather atlanta ga":
            return weather_payload
        return empty_payload

    monkeypatch.setattr(
        "adk_agent.skills.web_search.tools.web_search._fetch_brave_response",
        _fake_fetch,
    )

    result = BraveSearchClient().search(
        "current weather Atlanta GA right now temperature conditions precipitation wind",
        max_results=3,
    )

    assert seen_queries == [
        "current weather Atlanta GA right now temperature conditions precipitation wind",
        "weather atlanta ga",
    ]
    assert result.citations[0]["url"] == "https://example.com/atlanta-weather"
    assert "Atlanta weather" in result.answer_text


def test_query_variants_for_non_weather_queries_are_stable():
    assert _query_variants("OpenAI latest news") == ["OpenAI latest news"]


def test_query_variants_simplify_verbose_queries():
    assert _query_variants(
        "current weather Atlanta GA right now temperature conditions precipitation wind"
    ) == [
        "current weather Atlanta GA right now temperature conditions precipitation wind",
        "weather atlanta ga",
    ]


def test_debug_search_attempts_reports_attempt_metadata(monkeypatch):
    payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "Example",
            "url": "https://example.com/a",
            "description": "Snippet"
          }
        ]
      }
    }
    """

    monkeypatch.setattr(
        "adk_agent.skills.web_search.tools.web_search._fetch_brave_response",
        lambda query, max_results, verify: payload,
    )

    attempts = debug_search_attempts("example query", max_results=3)

    assert len(attempts) == 1
    assert attempts[0]["query"] == "example query"
    assert attempts[0]["results_count"] == 1
    assert "\"web\"" in attempts[0]["response"]


def test_debug_search_attempts_honors_insecure_ssl_fallback(monkeypatch):
    payload = b"""
    {
      "web": {
        "results": [
          {
            "title": "Example",
            "url": "https://example.com/a",
            "description": "Snippet"
          }
        ]
      }
    }
    """
    calls: list[bool] = []

    def _fake_fetch(query: str, max_results: int, verify: bool) -> bytes:
        del query, max_results
        calls.append(verify)
        if verify:
            raise RuntimeError("CERTIFICATE_VERIFY_FAILED")
        return payload

    monkeypatch.setenv("BRAVE_VERIFY", "1")
    monkeypatch.setenv("BRAVE_ALLOW_INSECURE_FALLBACK", "1")
    monkeypatch.setattr(
        "adk_agent.skills.web_search.tools.web_search._fetch_brave_response",
        _fake_fetch,
    )

    attempts = debug_search_attempts("example query", max_results=3)

    assert calls == [True, False]
    assert attempts[0]["results_count"] == 1
