
import json
from pathlib import Path
from typing import Optional
import typer
import pandas as pd
from tqdm import tqdm

from .io_excel import read_excel_any
from .counter import build_phrase_index, aggregate_by_date

app = typer.Typer(add_completion=False)

@app.command()
def parse(
    input_path: Path = typer.Argument(..., help="Файл или папка с .xlsx"),
    keywords: Path = typer.Option(..., '--keywords', '-k', help='TXT со словами/фразами, по 1 в строке'),
    out: Path = typer.Option(Path('outputs'), '--out', help='Папка для сохранения результатов'),
    lemma: bool = typer.Option(True, '--lemma/--no-lemma', help='Лемматизировать текст/ключи'),
    ordered_phrases: bool = typer.Option(False, '--ordered-phrases', help='Считать фразы только с учетом порядка'),
    top: int = typer.Option(50, '--top', help='Размер топа ключей')
):
    out.mkdir(parents=True, exist_ok=True)
    keys = [line.strip() for line in keywords.read_text(encoding='utf-8').splitlines() if line.strip()]
    phrase_index = build_phrase_index(keys, use_lemma=lemma, ordered=ordered_phrases)

    df = read_excel_any(input_path)
    if 'publish_date' not in df.columns or 'text' not in df.columns:
        raise typer.BadParameter("Ожидаются колонки publish_date и text в Excel" )

    by_date, top_df = aggregate_by_date(df, phrase_index, use_lemma=lemma, ordered=ordered_phrases)
    by_date.to_csv(out / 'by_date.csv', index=False)
    top_df.head(top).to_csv(out / 'top_keywords.csv', index=False)

    typer.echo(f'Готово. Файлы: {out / "by_date.csv"}, {out / "top_keywords.csv"}')

if __name__ == '__main__':
    app()
