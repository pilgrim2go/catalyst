#
# Copyright 2017 Enigma MPC, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

import pandas as pd

from six.moves.urllib.parse import urlencode

from catalyst.data.bundles.core import register_bundle
from catalyst.data.bundles.bundle import AbstractBundle
from catalyst.utils.memoize import lazyval

class PoloniexBundle(AbstractBundle):
    def __init__(self):
        super(self.__class__, self).__init__()

    @lazyval
    def name(self):
        return 'poloniex'

    @lazyval
    def exchange(self):
        return 'POLO'

    @lazyval
    def calendar_name(self):
        return 'OPEN'

    @lazyval
    def minutes_per_day(self):
        return 1440

    @lazyval
    def frequencies(self):
        return set((
            'daily',
        ))

    @lazyval
    def md_dtypes(self):
        return [
            ('symbol', 'object'),
            ('start_date', 'datetime64[ns]'),
            ('end_date', 'datetime64[ns]'),
            ('ac_date', 'datetime64[ns]'),
        ]

    @lazyval
    def dtypes(self):
        return [
            ('date', 'datetime64[ns]'),
            ('open', 'float64'),
            ('high', 'float64'),
            ('low', 'float64'),
            ('close', 'float64'),
            ('volume', 'float64'),
        ]

    @lazyval
    def tar_url(self):
        return (
            'https://www.dropbox.com/s/9naqffawnq8o4r2/'
            'poloniex-bundle.tar?dl=1'
        )

    @lazyval
    def wait_time(self):
        return pd.Timedelta(milliseconds=170)

    def fetch_raw_metadata_frame(self, api_key, page_number):
        if page_number > 1:
            return pd.DataFrame([])

        raw = pd.read_json(
            self._format_metadata_url(
              api_key,
              page_number,
            ),
            orient='index',
        )

        raw = raw.sort_index().reset_index()
        raw.rename(
            columns={'index':'symbol'},
            inplace=True,
        )

        return raw

    def post_process_symbol_metadata(self, metadata, data):
        start_date = data.index[0].tz_localize(None)
        end_date = data.index[-1].tz_localize(None)
        ac_date = end_date + pd.Timedelta(days=1)

        return (
            metadata.symbol,
            start_date,
            end_date,
            ac_date,
        )

    def fetch_raw_symbol_frame(self,
                               api_key,
                               symbol,
                               start_date,
                               end_date,
                               frequency):
        raw = pd.read_json(
            self._format_data_url(
                api_key,
                symbol,
                start_date,
                end_date,
                frequency,
            ),
            orient='records',
        )

        raw.set_index('date', inplace=True)

        scale = 1000.0
        raw.loc[:, 'open'] /= scale
        raw.loc[:, 'high'] /= scale
        raw.loc[:, 'low'] /= scale
        raw.loc[:, 'close'] /= scale
        raw.loc[:, 'volume'] *= scale

        return raw

    '''
    HELPER METHODS
    '''

    def _format_metadata_url(self, api_key, page_number):
        query_params = [
            ('command', 'returnTicker'),
        ]

        return self._format_polo_query(query_params)


    def _format_data_url(self,
                         api_key,
                         symbol,
                         start_date,
                         end_date,
                         data_frequency):
        period_map = {
            'daily': 86400,
            '5-minute': 300,
            'minute': 60,
        }

        try:
            period = period_map[data_frequency]
        except KeyError:
            return None

        query_params = [
            ('command', 'returnChartData'),
            ('currencyPair', symbol),
            ('start', start_date.value / 10**9),
            ('end', end_date.value / 10**9),
            ('period', period),
        ]
            
        return self._format_polo_query(query_params)
    
    def _format_polo_query(self, query_params):
        return 'https://poloniex.com/public?{query}'.format(
            query=urlencode(query_params),
        )

register_bundle(PoloniexBundle)