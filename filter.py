#!/usr/bin/env python3
import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterator, Union

from pandas import DataFrame, read_sql_query


class DBFilter:
    QUERY = f"SELECT * from dewolf"

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
        commit = self._df.dewolf_current_commit.loc[0]  # just take any commit for now
        failed_runs = self._df[self._df.is_successful == 0]
        summary = {
            "id": 0,
            "dewolf_current_commit": commit,
            "avg_dewolf_decompilation_time": self._df.dewolf_decompilation_time.dropna().mean(),
            "total_functions": len(self._df),
            "total_errors": len(failed_runs),
            "unique_exceptions": len(failed_runs.dewolf_exception.unique()),
            "unique_tracebacks": len(failed_runs.dewolf_traceback.unique()),
        }
        return DataFrame(summary, index=[0])

    def _get_filtered(self) -> DataFrame:
        """
        Filter dataset to contain 10 smallest cases per unique exception AND traceback
        generate case id for semantic grouping of similar errors. (e.g., ExceptionType@file.py:42)
        """
        f = lambda x: x.nsmallest(10, "function_basic_block_count")
        failed_runs = self._df[self._df.is_successful == 0]
        exception_counts = failed_runs["dewolf_exception"].value_counts()
        failed_runs["exception_count_pre_filter"] = failed_runs["dewolf_exception"].map(exception_counts)
        filtered_df = failed_runs.groupby(["dewolf_exception", "dewolf_traceback"]).apply(f)
        failed_runs["error_file_path"] = failed_runs["dewolf_traceback"].apply(self._get_last_file_path)
        failed_runs["error_line"] = failed_runs["dewolf_traceback"].apply(self._get_last_line_number)
        # case id: ExceptionType@file.py:42
        failed_runs["case_id"] = (
            failed_runs["dewolf_exception"].str.split().str[0].str.strip(": ")
            + "@"
            + failed_runs["error_file_path"].str.split("/").str[-1]
            + ":"
            + failed_runs["error_line"]
        )
        assert isinstance(filtered_df, DataFrame)
        return filtered_df.reset_index(drop=True)

    @staticmethod
    def _get_last_file_path(traceback: str) -> str:
        """Extract the last file path contained in a Traceback"""
        file_path, line, *_ = traceback.rpartition("File ")[-1].split(", ")
        return file_path.strip('"')

    @staticmethod
    def _get_last_line_number(traceback: str) -> str:
        """Return the line number (as str) from the last row of a Traceback"""
        file_path, line, *_ = traceback.rpartition("File ")[-1].split(", ")
        return line.lstrip("line ")

    @property
    def summary(self) -> DataFrame:
        if self._summary is None:
            self._summary = self._get_summary()
        return self._summary

    @property
    def filtered(self) -> DataFrame:
        if self._filtered is None:
            self._filtered = self._get_filtered()
        return self._filtered

    def write(self, file_path: Path):
        self._write_df_to_sqlite3(self.summary, file_path, "summary")
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
