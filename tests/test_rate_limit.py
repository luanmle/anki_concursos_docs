from types import SimpleNamespace

from starlette.requests import Request

from app.core import rate_limit


def request_for(ip_address: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/reports",
            "headers": [
                (b"x-forwarded-for", ip_address.encode("ascii")),
            ],
            "client": ("127.0.0.1", 12345),
        }
    )


def test_rate_limit_bounds_distinct_client_keys(monkeypatch) -> None:
    settings = SimpleNamespace(
        trust_proxy_headers=True,
        rate_limit_max_keys=100,
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: settings)

    for index in range(101):
        rate_limit._limit(
            request_for(f"198.51.100.{index}"),
            namespace="bounded",
            maximum=10,
            window_seconds=60,
            detail="limited",
        )

    assert len(rate_limit._attempts) == 100


def test_forwarded_header_is_ignored_when_proxy_is_not_trusted(
    monkeypatch,
) -> None:
    settings = SimpleNamespace(
        trust_proxy_headers=False,
        rate_limit_max_keys=100,
    )
    monkeypatch.setattr(rate_limit, "get_settings", lambda: settings)

    assert rate_limit._client_key(request_for("198.51.100.10")) == "127.0.0.1"
