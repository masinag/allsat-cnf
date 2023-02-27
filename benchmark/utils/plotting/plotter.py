from typing import Literal, Dict, List

import pandas as pd

from ..parsing import Mode

Param = Literal["time", "models"]


class Plotter:
    FONTSIZE = 10
    LINEWIDTH = 2.5
    FIGSIZE = (10, 8)

    def __init__(self, data: pd.DataFrame, output_dir: str, filename: str, colors: Dict[Mode, str], order: List[Mode]):
        self.data = data
        self.output_dir = output_dir
        self.filename = filename
        self.colors = colors
        self.order = order
        self.logscale = False

    def get_modes(self):
        avail_modes = {Mode(m) for m in self.data.columns.get_level_values(1).unique()}
        return [mode for mode in self.order if mode in avail_modes]
