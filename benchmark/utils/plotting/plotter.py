from typing import Literal, Dict, List, Optional

import pandas as pd

from ..parsing import Mode

Param = Literal["time", "models", "n_clauses"]


class Plotter:
    FONTSIZE = 22
    TICKSIZE = 16
    LINEWIDTH = 2.5
    FIGSIZE = (10, 8)

    def __init__(self, data: pd.DataFrame, output_dir: str, filename: str, colors: Dict[Mode, str], order: List[Mode],
                 timeout: Optional[int], timeout_models: Optional[int], name_mapping: Dict[Mode, str], linestyles: Dict[Mode, str]):
        self.data = data
        self.output_dir = output_dir
        self.filename = filename
        self.colors = colors
        self.order = order
        self.timeout = timeout
        self.timeout_models = timeout_models
        self.logscale = True
        self.name_mapping = name_mapping
        self.linestyles = linestyles
        for mode in self.order:
            if mode not in self.name_mapping:
                self.name_mapping[mode] = mode.value
            if mode not in self.linestyles:
                self.linestyles[mode] = "-"

    def get_modes(self):
        avail_modes = {Mode(m) for m in self.data.columns.get_level_values(1).unique()}
        return [mode for mode in self.order if mode in avail_modes]
