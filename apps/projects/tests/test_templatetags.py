"""Tests de los filtros de presentación."""

from apps.projects.templatetags.project_tags import stack_color


def test_stack_color_returns_specific_classes_for_known_tag():
    assert "emerald" in stack_color("Django")
    assert "sky" in stack_color("Docker")


def test_stack_color_falls_back_for_unknown_tag():
    result = stack_color("Cobol")

    assert "ink-" in result


def test_stack_color_differs_between_technologies():
    assert stack_color("Python") != stack_color("Go")
