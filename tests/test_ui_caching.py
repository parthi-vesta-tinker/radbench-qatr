"""The built UI must not be cached in a way that pins a browser to an old build."""

import pytest
from backend.main import DIST

pytestmark = pytest.mark.skipif(
    not (DIST / "index.html").is_file(),
    reason="frontend/dist is not built; run npm --prefix frontend run build",
)


def test_index_is_revalidated_on_every_load(client):
    # index.html names the content-hashed bundles. A cached copy keeps serving a build
    # that no longer exists, which is how a deployed change stays invisible.
    result = client.get("/")
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-cache"


def test_hashed_assets_stay_cacheable(client):
    names = [path.name for path in (DIST / "assets").glob("*.js")]
    assert names, "expected at least one hashed bundle in frontend/dist/assets"
    result = client.get(f"/assets/{names[0]}")
    assert result.status_code == 200
    assert result.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_api_responses_are_still_never_stored(client):
    # The existing /api/ rule must survive: it is stricter than the UI rule.
    result = client.get("/api/v1/status")
    assert result.status_code == 200
    assert result.headers["cache-control"] == "no-store"
