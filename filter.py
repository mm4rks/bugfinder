#!/usr/bin/env python3
import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterator, Union

from pandas import DataFrame, read_sql_query


class DBFilter:
    QUERY = f"SELECT * from dewolf WHERE is_successful = 0"

    def __init__(self, df: DataFrame):
        self._summary = None
        self._filtered = None
        self._df = df

    @classmethod
    def from_file(cls, file_path):
        with sqlite3.connect(file_path) as con:
            df = read_sql_query(cls.QUERY, con)
        return cls(df)

    @staticmethod
    def _write_df_to_sqlite3(df: DataFrame, database_path: Union[str, Path], table_name: str):
        with sqlite3.connect(database_path) as con:
            df.to_sql(table_name, con, index=False, if_exists="replace")

    def _get_summary(self) -> DataFrame:
        # current version 	TODO
        # samples 	5
        # functions 	11
        # errors 	11
        # ⌀ function size 	-1
        # ⌀ decompilation time 	-1s
        return DataFrame()

    def _get_filtered(self) -> DataFrame:
        f = lambda x: x.nsmallest(10, "function_basic_block_count")
        filtered_df = self._df.groupby("dewolf_exception").apply(f)
        assert isinstance(filtered_df, DataFrame)
        return filtered_df.reset_index(drop=True)

    @property
    def summary(self) -> DataFrame:
        if not self._summary:
            self._summary = self._get_summary()
        return self._summary

    @property
    def filtered(self) -> DataFrame:
        if not self._filtered:
            self._filtered = self._get_filtered()
        return self._filtered

    def write(self, file_path: Path):
        # self._write_df_to_sqlite3(self.summary, file_path, "summary")
        self._write_df_to_sqlite3(self.filtered, file_path, "dewolf")


def existing_file(path):
    """Check if the provided path is an existing file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist.")
    return file_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bug finding tool for dewolf decompiler")
    parser.add_argument("-i", "--input", required=True, type=existing_file, help="Path to SQLite file")
    parser.add_argument("-o", "--output", required=True, type=Path, help="File path of filtered output (SQLite file)")
    parser.add_argument("--verbose", "-v", dest="verbose", action="count", help="Set logging verbosity (-vvv)", default=0)
    return parser.parse_args()


def main(args: argparse.Namespace) -> int:
    f = DBFilter.from_file(args.input)
    f.write(args.output)
    return 0


if __name__ == "__main__":
    args = parse_arguments()
    sys.exit(main(args))
