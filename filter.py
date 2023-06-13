#!/usr/bin/env python3
import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterator, Union

from pandas import DataFrame, read_sql_query, unique, to_datetime


class DBFilter:
    QUERY = "SELECT * from dewolf" # query to read from samples.sqlite3
    ISSUE_SCHEMA = """CREATE TABLE IF NOT EXISTS samples_githubissue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_group TEXT,
            title TEXT,
            description TEXT,
            status VARCHAR(100),
            number INTEGER,
            html_url TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
    def __init__(self, df: DataFrame):
        self._summary = None
        self._filtered = None
        self._samples = None
        self._df = df

    @classmethod
    def from_file(cls, file_path):
        with sqlite3.connect(file_path) as con:
            df = read_sql_query(cls.QUERY, con)
        return cls(df)

    @staticmethod
    def _write_df_to_sqlite3(df: DataFrame, database_path: Union[str, Path], table_name: str):
        """
        Write DataFrame to SQLite table
        """
        dtype_mapping = {
            'int64': 'INTEGER',
            'float64': 'REAL',
            'bool': 'INTEGER',         # SQLite uses INTEGER for boolean values
            'datetime64[ns]': 'TEXT',  # SQLite does not have a separate datetime type
            'object': 'TEXT'           # For all other non-numeric types
        }
        dtype = {name: dtype_mapping.get(str(dt), "TEXT") for name, dt in df.dtypes.items()}
        dtype["id"] = "INTEGER NOT NULL PRIMARY KEY"
        with sqlite3.connect(database_path) as con:
            df.sort_values("id").to_sql(table_name, con, index=False, if_exists="replace", dtype=dtype)

    def _get_summary(self) -> DataFrame:
        """
        Return DataFrame containing summary statistics over all samples
        """
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
            "processed_samples": len(self._df.sample_hash.unique()),
        }
        return DataFrame(summary, index=[0])

    def _get_filtered(self) -> DataFrame:
        """
        Filter dataset to contain 10 smallest cases per unique exception AND traceback
        generate case id for semantic grouping of similar errors. (e.g., ExceptionType@file.py:42)
        """
        failed_runs = self._df[self._df.is_successful == 0].copy()
        # enrich dewolf errors data
        failed_runs["error_file_path"] = failed_runs["dewolf_traceback"].apply(self._get_last_file_path)
        failed_runs["error_line"] = failed_runs["dewolf_traceback"].apply(self._get_last_line_number)
        # case id: ExceptionType@file.py:42
        failed_runs["case_group"] = (
                failed_runs["dewolf_exception"].str.split().str[0].str.strip(": ")
                + "@"
                + failed_runs["error_file_path"].str.split("/").str[-1]
                + ":"
                + failed_runs["error_line"]
                )
        errors_per_group_count = failed_runs["case_group"].value_counts()
        failed_runs["errors_per_group_count_pre_filter"] = failed_runs["case_group"].map(errors_per_group_count)
        # filter n smallest unique per exception and traceback
        f = lambda x: x.nsmallest(10, "function_basic_block_count")
        filtered_df = failed_runs.groupby(["dewolf_exception", "dewolf_traceback"]).apply(f)
        assert isinstance(filtered_df, DataFrame)
        return filtered_df.reset_index(drop=True)

    def _get_samples(self) -> DataFrame:
        """
        Return DataFrame containing per sample statistics
        """
        self._df["timestamp"] = to_datetime(self._df["timestamp"])
        unique_lst_to_str = lambda x: ",".join(iter(unique(x)))
        samples = (
            self._df.groupby(["sample_hash", "dewolf_current_commit"])
                .agg(
                    platform=("function_platform", unique_lst_to_str),
                    binaryninja_version=("binaryninja_version", unique_lst_to_str),
                    count_error=("is_successful", lambda x: sum(x == 0)),
                    count_success=("is_successful", lambda x: sum(x == 1)),
                    count_total_processed=("is_successful", "count"),
                    timestamp=("timestamp", "min"),
                    duration_seconds=("timestamp", lambda x: (x.max() - x.min()).total_seconds()),
                    dewolf_max_basic_blocks=("dewolf_max_basic_blocks", lambda x: x.iloc[0]),
                    sample_total_function_count=("sample_total_function_count", lambda x: x.iloc[0]),
                    sample_decompilable_function_count=("sample_decompilable_function_count", lambda x: x.iloc[0])
                )
                .reset_index()
            )
        samples["id"] = samples.index
        return samples

    @staticmethod
    def _get_last_file_path(traceback: str) -> str:
        """Extract the last file path contained in a Traceback"""
        file_path, _, *_ = traceback.rpartition("File ")[-1].split(", ")
        return file_path.strip('"')

    @staticmethod
    def _get_last_line_number(traceback: str) -> str:
        """Return the line number (as str) from the last row of a Traceback"""
        _, line, *_ = traceback.rpartition("File ")[-1].split(", ")
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

    @property
    def samples(self) -> DataFrame:
        if self._samples is None:
            self._samples = self._get_samples()
        return self._samples

    def write(self, file_path: Path):
        self._write_df_to_sqlite3(self.summary, file_path, "summary")
        self._write_df_to_sqlite3(self.filtered, file_path, "dewolf_errors")
        self._write_df_to_sqlite3(self.samples, file_path, "samples")

        # create issue table
        with sqlite3.connect(file_path) as con:
            cursor = con.cursor()
            cursor.execute(self.ISSUE_SCHEMA)
            con.commit()



def print_sample_hashes(db_file: Path):
    """Print all sample hashes contained in DB file"""
    sample_hashes = set()
    COLUMN = "sample_hash"
    with sqlite3.connect(db_file) as con:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()
        for table in table_names:
            table_name = table[0]
            logging.info(f"read from {table_name}")
            # Check if the column exists
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = {column[1] for column in cursor.fetchall()}
            if COLUMN in columns:
                cursor.execute(f"SELECT DISTINCT {COLUMN} FROM {table_name};")
                sample_hashes.update(h[0] for h in cursor.fetchall())
        cursor.close()
    for s in sample_hashes:
        print(s)


def existing_file(path):
    """Check if the provided path is an existing file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise argparse.ArgumentTypeError(f"File '{path}' does not exist.")
    return file_path


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bug finding tool for dewolf decompiler")
    parser.add_argument("-i", "--input", required=True, type=existing_file, help="Path to SQLite file")
    parser.add_argument("-o", "--output", default="filtered.sqlite3", type=Path, help="File path of filtered output (SQLite file, default: filtered.sqlite3)")
    parser.add_argument("-l", "--list", action="store_true", help="List sample hashes contained in SQLite DB")
    # TODO
    # parser.add_argument("--verbose", "-v", dest="verbose", action="count", help="Set logging verbosity (-vvv)", default=0)
    return parser.parse_args()


def main(args: argparse.Namespace) -> int:
    if args.list:
        print_sample_hashes(args.input)
        return 0
    logging.info("filtering database")
    f = DBFilter.from_file(args.input)
    f.write(args.output)
    return 0


if __name__ == "__main__":
    args = parse_arguments()
    sys.exit(main(args))
