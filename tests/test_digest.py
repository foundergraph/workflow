import pytest
from fgai_workflows.digest import MorningDigest

def test_morning_digest_initialization():
    md = MorningDigest(tz="UTC")
    assert md.tz == "UTC"