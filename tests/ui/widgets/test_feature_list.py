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
