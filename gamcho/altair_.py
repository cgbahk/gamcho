import numpy as np
import pandas as pd
import altair as alt
from math import sqrt


def get_heatmap_for_2D(tensor):
    """
    axis[0]: row    or y
    axis[1]: column or x
    """
    # TODO Support tensor as numpy or torch

    assert len(tensor.shape) == 2

    num_row = tensor.shape[0]
    num_col = tensor.shape[1]

    col, row = np.meshgrid(range(num_col), range(num_row))

    frame = pd.DataFrame({'column': col.ravel(), 'row': row.ravel(), 'value': tensor.ravel()})

    return alt.Chart(frame).mark_rect().encode(x="column:O", y="row:O", color="value:Q")


def auto_concat(charts, *, height=None, width=None):
    """
    charts: List of alt.Chart
    height/width: Desired count of chart for each
                  By default, infer automatic value with golden ratio
    """
    num_chart = len(charts)
    assert num_chart > 0

    if (height, width) == (None, None):
        height, width = 0, 0

        golden_ratio = (1 + sqrt(5)) / 2

        while height * width < num_chart:
            height += 1
            width = round(golden_ratio * height)

    # TODO Support other case of (height, width): (None, Valid), (Valid, None)

    assert isinstance(height, int)
    assert height > 0

    assert isinstance(width, int)
    assert width > 0

    assert height * width >= num_chart

    ret = alt.vconcat()
    for vertical_idx in range(height):
        ret &= alt.hconcat(*charts[vertical_idx * width:(vertical_idx + 1) * width])

    return ret
