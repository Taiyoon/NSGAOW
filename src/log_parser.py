# old log
from datetime import date, datetime, timedelta
from functools import cached_property
from io import StringIO
from typing import Literal

import pandas as pd
from numpy import datetime64, timedelta64
from pandas import DataFrame
from pandas.core.groupby.generic import DataFrameGroupBy


class Parser:
    def __init__(self, path: str | StringIO) -> None:
        self.df = self.load_log(path)

    @staticmethod
    def load_log(path: str | StringIO) -> pd.DataFrame:
        if isinstance(path, StringIO):
            path.seek(0)
        df = pd.json_normalize(
            pd.read_json(path, lines=True).to_dict('records'))
        return df

    @cached_property
    def cooptask_groups(self) -> DataFrameGroupBy:
        return self.df[self.df['record.extra.type'] == 'CoopTask'].groupby('record.extra.id')

    @cached_property
    def cooptask_finishtime(self) -> pd.DataFrame:
        return self.cooptask_groups.agg(finish_time=('record.extra.simtime', lambda x: x.max() - x.min()))

    @cached_property
    def cooptask_estimate_finish_time(self) -> pd.DataFrame:
        return self.df[self.df['record.message'] == 'estimate finish time']\
            .rename(columns={'record.extra.estimate_finish_time': 'estimate_finish_time'})[['estimate_finish_time', 'record.extra.task.id']]

    @cached_property
    def cooptask_time(self) -> pd.DataFrame:
        return self.cooptask_finishtime\
            .merge(self.cooptask_estimate_finish_time,
                   'outer', left_on='record.extra.id', right_on='record.extra.task.id')\
            .assign(estimate_error=lambda x: (x['estimate_finish_time'] - x['finish_time']) / x['finish_time'])
