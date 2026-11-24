"""Download the public historical freeCodeCamp survey; no synthetic fallback."""
from pathlib import Path
from urllib.request import urlretrieve
import os
import tempfile
from analyze import load

URL = ('https://raw.githubusercontent.com/freeCodeCamp/2017-new-coder-survey/'
       'master/clean-data/2017-fCC-New-Coders-Survey-Data.csv')
RAW = Path(__file__).resolve().parents[1]/'data'/'raw'


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    dest = RAW/'fcc_survey_2017.csv'
    if dest.exists():
        load(dest); print(f'Already downloaded: {dest}'); return dest
    fd, name = tempfile.mkstemp(dir=RAW,suffix='.part'); os.close(fd)
    try:
        urlretrieve(URL,name)
        load(Path(name))
        os.replace(name,dest)
    finally:
        Path(name).unlink(missing_ok=True)
    print(f'Saved -> {dest}'); return dest


if __name__=='__main__':
    main()
