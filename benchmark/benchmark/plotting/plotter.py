from typing import Literal

import pandas as pd

from ..mode import Mode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...plot import Style

Param = Literal["time", "models", "n_clauses"]


class Plotter:
    FONTSIZE = 22
    TICKSIZE = 16
    LINEWIDTH = 2.5
    FIGSIZE = (10, 8)

    def __init__(self, data: pd.DataFrame, output_dir: str, filename: str, timeout: int | None,
                 timeout_models: int | None, mode_styles: dict[Mode, "Style"], problem_set_styles: dict[str, "Style"]):
        self.data = data
        self.output_dir = output_dir
        self.filename = filename
        self.timeout = timeout
        self.timeout_models = timeout_models
        self.logscale = True
        self.mode_styles = mode_styles
        self.problem_set_styles = problem_set_styles

    def get_modes(self):
        avail_modes = [mode for m in self.data.columns.get_level_values(1).unique() if
                       (mode := Mode(m)) in self.mode_styles]
        return sorted(avail_modes, key=lambda x: self.mode_styles[x].order_index)

    def get_problem_sets(self):
        avail_ps = [p for p in self.data.index.get_level_values(0).unique() if p in self.problem_set_styles]
        return sorted(avail_ps, key=lambda x: self.problem_set_styles[x].order_index)
