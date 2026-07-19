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


def test_render_strips_script_tags(tmp_path):
    # Los README vienen de repos clonados: HTML crudo malicioso no debe sobrevivir.
    (tmp_path / "README.md").write_text("# Título\n\n<script>alert(1)</script>\n", encoding="utf-8")

    html = readme.render(tmp_path)

    assert "<script" not in html
    assert "<h1" in html  # el contenido legítimo sí se renderiza


def test_render_rewrites_relative_image_paths(tmp_path):
    # El navegador resolvería la ruta contra la raíz del panel, donde no hay nada.
    (tmp_path / "README.md").write_text("![captura](screenshots/demo.png)\n", encoding="utf-8")

    html = readme.render(tmp_path, asset_base="/3/readme/asset/")

    assert 'src="/3/readme/asset/screenshots/demo.png"' in html


def test_render_leaves_absolute_image_urls_alone(tmp_path):
    (tmp_path / "README.md").write_text(
        "![remota](https://ejemplo.com/x.png)\n![badge](/static/y.png)\n", encoding="utf-8"
    )

    html = readme.render(tmp_path, asset_base="/3/readme/asset/")

    assert 'src="https://ejemplo.com/x.png"' in html
    assert 'src="/static/y.png"' in html


def test_render_without_asset_base_keeps_paths(tmp_path):
    (tmp_path / "README.md").write_text("![c](img/a.png)\n", encoding="utf-8")

    assert 'src="img/a.png"' in readme.render(tmp_path)


def test_render_strips_event_handlers(tmp_path):
    (tmp_path / "README.md").write_text('<img src="x" onerror="alert(1)">\n', encoding="utf-8")

    html = readme.render(tmp_path)

    assert "onerror" not in html
