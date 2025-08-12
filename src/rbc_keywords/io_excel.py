
import pandas as pd
from pathlib import Path
from typing import Union, List

def read_excel_any(path: Union[str, Path]) -> pd.DataFrame:
    path = Path(path)
    if path.is_dir():
        frames: List[pd.DataFrame] = []
        for p in sorted(path.glob('*.xlsx')):
            frames.append(pd.read_excel(p))
        if not frames:
            raise FileNotFoundError(f'Не найдено .xlsx в {path}')
        return pd.concat(frames, ignore_index=True)
    return pd.read_excel(path)
