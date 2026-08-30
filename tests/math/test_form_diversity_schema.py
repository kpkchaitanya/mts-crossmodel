"""Schema coverage for optional Form Diversity question metadata."""
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_worksheet_spec_schema_declares_form_diversity_metadata():
    schema = json.loads((REPO / "schemas" / "worksheet-spec.schema.json").read_text(encoding="utf-8"))
    properties = schema["properties"]["items"]["items"]["properties"]
    assert properties["form_family"] == {"type": "string"}
    assert properties["cognitive_action"] == {"type": "string"}
    assert properties["representation"] == {"type": "string"}
    assert properties["response_type"] == {"type": "string"}
    assert properties["variation_seed"] == {"type": "integer"}