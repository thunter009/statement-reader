"""Console script for statement_reader."""
import logging
import sys
from email.policy import default
from pathlib import Path

import click

from statement_reader.core import Input
from statement_reader.providers import (
    CapitalOneCheckingTransactions,
    VanguardActivitySummary,
)
from statement_reader.settings import (
    LOGGING_DATE_FORMAT,
    LOGGING_FORMAT,
    LOGGING_PATH,
    VALID_PROVIDER_TYPES,
    VALID_PROVIDERS,
)

FILE_NAME = __name__
logging.basicConfig(level=logging.INFO,
                    datefmt=LOGGING_DATE_FORMAT,
                    format=LOGGING_FORMAT,
                    handlers=[
                        logging.FileHandler(
                            f"{LOGGING_PATH}/{FILE_NAME}.log",
                            encoding=None,
                            delay=False),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger()


class Config:
    """Configuration Object"""
CONTEXT = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.argument('provider', type=click.Choice(VALID_PROVIDERS, case_sensitive=False))
@CONTEXT
def cli(ctx,
        provider):
    '''
        Statement Reader CLI

        Python/click based CLI to parse + process common financial institution account and transaction statements.

        Input options:
        - local pdf

        Output options:
        - local csv
    '''
    ctx.provider = provider

@cli.command('convert')
@click.argument('type', type=click.Choice(VALID_PROVIDER_TYPES, case_sensitive=False))
@click.option('-i', '--input', "_input", type=str)
@click.option('-o', '--output', "_output", type=str, default=".")
@CONTEXT
def convert(ctx,
            type,
            _input,
            _output):
    '''
        Converts the tables from an input pdf to csv files. Defaults to one aggregated csv per input pdf
    '''
    provider = ctx.provider

    input_files = Input(_input)

    if provider == 'capitalone':
        
        if type == 'checking':
            checking = CapitalOneCheckingTransactions(input_files)
    
    if provider == 'vanguard':
        
        if type == 'activity-summary':
            activity_summary = VanguardActivitySummary(input_files)

        


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
