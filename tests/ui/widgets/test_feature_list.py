from __future__ import annotations

from installer_framework.config.models import FeatureConfig
from installer_framework.ui.widgets.feature_list import FeatureListWidget


def test_feature_list_filter_and_selection(qtbot):
    features = [
        FeatureConfig(id="core", label="Core", default=True),
        FeatureConfig(id="docs", label="Docs", default=False),
    ]
    widget = FeatureListWidget(features=features, selected=["docs"])
    qtbot.addWidget(widget)
    widget.show()

    selected = widget.get_selected()
    assert "core" in selected
    assert "docs" in selected

    widget.search.setText("core")
    widget._apply_filter("core")
    visible = [not row.isHidden() for _feature, row, _cb in widget.rows]
    assert any(visible)


def test_feature_list_applies_explicit_background_styles(qtbot):
    features = [FeatureConfig(id="core", label="Core", default=True)]
    widget = FeatureListWidget(features=features)
    qtbot.addWidget(widget)

    assert "background-color" in widget.scroll.styleSheet()
    assert "background-color" in widget.scroll.viewport().styleSheet()
    assert "background-color" in widget.scroll_container.styleSheet()
    assert "background-color" in widget.rows[0][1].styleSheet()
