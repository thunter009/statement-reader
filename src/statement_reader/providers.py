import pdb
from dataclasses import dataclass, field

import camelot
import pandas as pd
from camelot.core import Table
from pandas import DataFrame, RangeIndex
from pandas.testing import assert_frame_equal

from statement_reader.core import Input, Metadata
from statement_reader.exceptions import InaccuratePDFRead
from statement_reader.utils import default_field


@dataclass
class BaseProvider(Metadata):
    """
    A base financial institution service provider object which takes an Input object. Inherited by specific provider implementation objects.
    """
    input: Input = field(repr=False)
    output: DataFrame = default_field(None, init=False, repr=False)

    @staticmethod
    def check_accuracy(table: Table, threshold: int = 50):
        """
        Ensures a high accuracy parse
        """
        accuracy = table.parsing_report['accuracy']
        if accuracy < threshold:
            raise InaccuratePDFRead


@dataclass
class Vanguard(BaseProvider):
    """
    Vanguard base service provider.

    Supports different types of Vanguard reports and can detect 
    them based on input in some limited cases/
    """
    name: str = default_field("vanguard", init=False, repr=False)
    type: str = default_field(None, init=False)

    def __post_init__(self):
        self.data = self.load()

    @staticmethod
    def is_cover_page_table(df: DataFrame) -> bool:
        """
        Detects a common cover page on Vanguard reports which can somtimes be parsed as a table by camelot.

        df: a pandas DataFrame object that is produced from a camelot pdf read
        """
        selector = [
            ['This statement reflects activity at and/or assets held by separate entities. Brokerage'],
            ['assets are held by Vanguard Brokerage Services® (VBS), a division of Vanguard Marketing'],
            ['Corporation (VMC), member FINRA and SIPC. VMC is a wholly owned subsidiary of The'],
            ['Vanguard Group, Inc. (VGI). Vanguard funds not held through your VBS account are held by'],
            ['VGI and are not protected by SIPC. Summary data are provided solely as a service and are'],
            ['for informational purposes only. If applicable, portfolio allocation consists of Vanguard'],
            ['funds and brokerage assets. For a complete listing of your brokerage assets, refer to the'],
            ['section titled "Balances and holdings."']
        ]
        df_selector = pd.DataFrame(selector)
        try:
            assert_frame_equal(df, df_selector)
        except AssertionError:
            return False
        return True


@dataclass
class VanguardActivitySummary(Vanguard):
    """
    Vanguard account activity summary parser.

    If this class parses an input that does not contain an activity 
    summary table for the account, then the data attribute will be None
    """
    type: str = default_field("activity-summary", init=False)

    def load(self):
        tables = camelot.read_pdf(
                                self.input.resolved_path, 
                                flavor = 'stream', 
                                # split_text=True,
                                # row_tol=10,
                                pages='1-end')
        for table in tables:
            self.check_accuracy(table)
            df = table.df

            if self.is_cover_page_table(df):
                continue

            if isinstance(df.columns, RangeIndex):
                pass
        return tables
