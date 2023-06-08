import logging.config

logger = logging.getLogger()

from dataclasses import dataclass

import camelot
import numpy as np
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

    input: Input = default_field(None, repr=False)
    output: DataFrame = default_field(None, init=False, repr=False)

    @staticmethod
    def check_accuracy(table: Table, threshold: int = 50):
        """
        Ensures a high accuracy parse
        """
        accuracy = table.parsing_report["accuracy"]
        logger.info(f"PDF Parse accuracy: {accuracy}")
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
            [
                "This statement reflects activity at and/or assets held by separate entities. Brokerage"
            ],
            [
                "assets are held by Vanguard Brokerage Services® (VBS), a division of Vanguard Marketing"
            ],
            [
                "Corporation (VMC), member FINRA and SIPC. VMC is a wholly owned subsidiary of The"
            ],
            [
                "Vanguard Group, Inc. (VGI). Vanguard funds not held through your VBS account are held by"
            ],
            [
                "VGI and are not protected by SIPC. Summary data are provided solely as a service and are"
            ],
            [
                "for informational purposes only. If applicable, portfolio allocation consists of Vanguard"
            ],
            [
                "funds and brokerage assets. For a complete listing of your brokerage assets, refer to the"
            ],
            ['section titled "Balances and holdings."'],
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
        """
        Load data into a list of pandas dataframes
        """
        tables = camelot.read_pdf(
            self.input.resolved_path,
            flavor="stream",
            # split_text=True,
            # row_tol=10,
            pages="1-end",
        )
        for table in tables:
            self.check_accuracy(table)
            df = table.df

            if self.is_cover_page_table(df):
                continue

            if isinstance(df.columns, RangeIndex):
                pass
        return tables


@dataclass
class CapitalOne(BaseProvider):
    """
    Capital One service provider.

    Supports different types of Capital One reports and can detect
    them based on input in some limited cases/
    """

    name: str = default_field("capitalone", init=False, repr=False)
    type: str = default_field(None, init=False)

    def __post_init__(self):
        self.data = self.load()

    def load(self):
        """
        Load data into a list of pandas dataframes
        """
        holder = []
        tables = camelot.read_pdf(
            self.input.resolved_path, flavor="stream", pages="1-end"
        )
        for table in tables:
            self.check_accuracy(table)
            df = table.df
            holder.append(df)

        return holder


@dataclass
class CapitalOneCheckingTransactions(CapitalOne):
    """
    Capital One checking account transaction history parser.
    """

    _PAGE_1_SELECTOR = pd.DataFrame(
        {
            0: ["DATE"],
            1: ["DESCRIPTION"],
            2: ["CATEGORY"],
            3: [""],
            4: ["AMOUNT"],
            5: ["BALANCE"],
        }
    )
    _PAGE_2_SELECTOR = pd.DataFrame(
        {
            0: ["DATE"],
            1: ["DESCRIPTION"],
            2: ["CATEGORY"],
            3: ["AMOUNT"],
            4: ["BALANCE"],
        }
    )

    type: str = default_field("checking", init=False)

    def __post_init__(self):
        super().__post_init__()
        # write method to grab statement effective date from cover page
        self._reduce_internal_data()
        breakpoint()

    def _reduce_internal_data(self):
        """
        Reduces the data property to only contain dataframes that are likely checking
        account transaction tables
        """
        holder = []
        for df in self.data:

            if self.is_checking_transactions_table(df, self._PAGE_1_SELECTOR):
                df = self.clean_transaction_table(df)
                holder.append(df)

        self.data = pd.concat(holder)

    def _select_page_one(self, df: DataFrame):
        """
        Selects page 1 of transaction table. If it finds a match, returns a dataframe with
        renamed columns
        """

        new_header_row = df[
            np.isin(df, self._PAGE_1_SELECTOR).all(axis=1)
        ].index.values[0]
        df_page_one = df.iloc[new_header_row + 1 : len(df)].rename(
            columns={k: v[0] for k, v in self._PAGE_1_SELECTOR.iteritems()}
        )
        return df_page_one

    def _select_page_two(self, df: DataFrame):
        """
        Selects page 2 of transaction table. If it finds a match, returns a dataframe with
        renamed columns
        """
        breakpoint()
        new_header_row = df[
            np.isin(df, self._PAGE_2_SELECTOR).all(axis=1)
        ].index.values[0]
        df_page_two = df.iloc[new_header_row + 1 : len(df)].rename(
            columns={k: v[0] for k, v in self._PAGE_2_SELECTOR.iteritems()}
        )
        return df_page_two

    def clean_transaction_table(self, df: DataFrame):
        """
        df: Transaction dataframe to clean
        """
        # drop extra header rows, rename columns to pre-determined header, reset index, and
        # replace empty strings with nans
        # drop unused column
        df_page_one = self._select_page_one(df)
        breakpoint()
        df_page_two = self._select_page_two(df)

        for dataframe in [df_page_one, df_page_two]:

            dataframe.reset_index(drop=True).replace(r"^\s*$", np.nan, regex=True).drop(
                columns=[""]
            )

            # properly parse date, category, and USD columns
            dataframe = dataframe.astype({"CATEGORY": "category"})
            dataframe["DATE"] = pd.to_datetime(dataframe["DATE"], format="%b %d")
            for column in ["AMOUNT", "BALANCE"]:
                try:
                    dataframe[column] = dataframe[column].replace(
                        r"[\$, +]", "", regex=True
                    )
                except KeyError:
                    continue

    @staticmethod
    def is_checking_transactions_table(df: DataFrame, df_compare: DataFrame) -> bool:
        """
        Looks for indicators that a given table is a capital one checking account
        transaction table.

        df: a pandas DataFrame that is an output of parsing the input pdf via camelot
        df_dataframe: a pandas Dataframe to be compared against df for similarity. If the
                           same then this is considered a transactions table.
        """
        return not df[np.isin(df, df_compare).all(axis=1)].index.empty
