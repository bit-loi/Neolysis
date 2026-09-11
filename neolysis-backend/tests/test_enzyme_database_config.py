from app.config import Settings


def test_neon_url_is_normalized_for_asyncpg():
    url = Settings._async_database_url(
        "postgresql://user:secret@example.neon.tech/db?sslmode=require&channel_binding=require"
    )

    assert url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in url
    assert "sslmode" not in url
    assert "channel_binding" not in url
