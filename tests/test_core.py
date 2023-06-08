#!/usr/bin/env python

"""Tests for `statement_reader` package."""

import pytest
from click.testing import CliRunner

from statement_reader import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    assert result.exit_code == 0
    expected_help_message = """Usage: cli [OPTIONS] {vanguard|capitalone} COMMAND [ARGS]...\n\n  Statement Reader CLI\n\n  CLI tool to parse and process common financial institution account and\n  transaction statements into usable data files.\n\n  Input options: - local pdf\n\n  Output options: - local csv\n\nOptions:\n  --help  Show this message and exit.\n\nCommands:\n  convert  Converts the tables from an input pdf to csv files.\n"""
    assert expected_help_message in result.output
    help_result = runner.invoke(cli.cli, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output


class TestInput:
    pass
