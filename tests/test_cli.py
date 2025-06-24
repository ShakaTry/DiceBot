import subprocess
import sys

from DiceBot import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "DiceBot", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
