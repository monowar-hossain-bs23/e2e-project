"""Tests for base template and brand design tokens."""

from django.template import Context, Template
from django.template.loader import render_to_string


def test_base_template_renders() -> None:
    """Verifies that templates/base.html renders without template syntax errors."""
    rendered = render_to_string("base.html", {})
    assert "<!doctype html>" in rendered
    assert "Basha Pass" in rendered
    assert "bootstrap@5.3.3" in rendered
    assert "bootstrap-icons" in rendered
    assert "brand-tokens.css" in rendered


def test_base_template_blocks() -> None:
    """Verifies that child templates can extend base.html and populate blocks."""
    child_template_str = """
    {% extends "base.html" %}
    {% block title %}Custom Title{% endblock %}
    {% block content %}
    <main><p>Custom Content Body</p></main>
    {% endblock %}
    """
    template = Template(child_template_str)
    rendered = template.render(Context({}))

    assert "<title>Custom Title</title>" in rendered
    assert "<main><p>Custom Content Body</p></main>" in rendered
