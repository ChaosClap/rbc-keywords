
from functools import lru_cache
import pymorphy2
from razdel import tokenize

_morph = pymorphy2.MorphAnalyzer()

@lru_cache(maxsize=200_000)
def lemmatize(token: str) -> str:
    if not token:
        return token
    return _morph.parse(token.lower())[0].normal_form

def tokenize_words(text: str):
    # Разделяем на токены-слова (буквы/цифры), без пунктуации
    for t in tokenize(text or ""):
        tok = t.text.strip()
        if tok:
            yield tok
