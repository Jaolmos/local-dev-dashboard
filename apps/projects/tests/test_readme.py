"""Tests del renderizado de README a HTML."""

from apps.projects.services import readme


def test_render_without_readme_returns_none(tmp_path):
    assert readme.render(tmp_path) is None


def test_render_converts_markdown_to_html(tmp_path):
    (tmp_path / "README.md").write_text("# Hola\n\nUn **párrafo**.\n", encoding="utf-8")

    html = readme.render(tmp_path)

    assert "<h1" in html
    assert "<strong>párrafo</strong>" in html


def test_render_supports_fenced_code_blocks(tmp_path):
    (tmp_path / "README.md").write_text("```python\nprint('hi')\n```\n", encoding="utf-8")

    html = readme.render(tmp_path)

    assert "<code" in html
