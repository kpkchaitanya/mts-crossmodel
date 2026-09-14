from pathlib import Path
import importlib.util


REPO = Path(__file__).resolve().parents[2]


def load_publish_module():
    module_path = REPO / "scripts" / "publish_weekly_artifacts.py"
    spec = importlib.util.spec_from_file_location("publish_weekly_artifacts", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_rendered_artifacts_requires_render_record(tmp_path):
    module = load_publish_module()
    try:
        module.load_rendered_artifacts(tmp_path)
    except FileNotFoundError as error:
        assert "rendered-artifacts.json" in str(error)
    else:
        raise AssertionError("Publishing must require rendered artifacts.")


def test_load_rendered_artifacts_returns_artifact_list(tmp_path):
    module = load_publish_module()
    (tmp_path / "rendered-artifacts.json").write_text(
        '{"artifacts": [{"worksheet_id": "grade_1"}]}\n',
        encoding="utf-8",
    )
    assert module.load_rendered_artifacts(tmp_path) == [{"worksheet_id": "grade_1"}]
