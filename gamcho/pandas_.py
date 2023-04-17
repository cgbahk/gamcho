import pandas as pd

from openpyxl.utils import get_column_letter


def save_excel(df: pd.DataFrame, path, **kwargs):
    """
    Wrapper for pandas `to_excel()`

    Feature:
    - Adjust column width automatically
    """

    sheet_name = kwargs.get("sheet_name", "Sheet1")  # pandas' default

    with pd.ExcelWriter(path) as writer:
        df.to_excel(
            writer,
            **kwargs,
        )

        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            col_letter = get_column_letter(col_idx + 1)

            # This may only work with `openpyxl` engine
            writer.sheets[sheet_name].column_dimensions[col_letter].width = column_width
