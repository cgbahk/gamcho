import numpy as np
import pandas as pd
import altair as alt


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
