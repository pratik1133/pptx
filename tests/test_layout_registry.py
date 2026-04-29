from reportgen.rendering.layout_registry import LAYOUT_REGISTRY, get_layout_definition


def test_layout_registry_contains_core_layouts() -> None:
    assert "cover_slide" in LAYOUT_REGISTRY
    assert "text_plus_chart" in LAYOUT_REGISTRY
    assert "disclaimer" in LAYOUT_REGISTRY


def test_text_plus_chart_requires_text_and_chart() -> None:
    layout = get_layout_definition("text_plus_chart")
    requirements = {item.block_type: (item.min_count, item.max_count) for item in layout.required_blocks}

    assert requirements["text"] == (1, 1)
    assert requirements["chart"] == (1, 1)
