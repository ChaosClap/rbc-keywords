
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Set
from .morph import tokenize_words, lemmatize

@dataclass
class MatchStats:
    total_hits: int
    texts_with_hits: int
    row_indices: List[int]

def normalize_phrase(phrase: str, use_lemma: bool) -> Tuple[str, ...]:
    tokens = list(tokenize_words(phrase))
    if use_lemma:
        tokens = [lemmatize(t) for t in tokens]
    return tuple(tokens)

def build_phrase_index(key_phrases: Iterable[str], use_lemma: bool, ordered: bool=False):
    # Храним как множества лемм для неупорядоченных фраз, либо как кортеж для упорядоченных
    idx = []
    for kp in key_phrases:
        norm = normalize_phrase(kp, use_lemma)
        if not norm:
            continue
        if ordered:
            idx.append((kp, norm))
        else:
            idx.append((kp, frozenset(norm)))
    return idx

def text_hits(text: str, phrase_index, use_lemma: bool, ordered: bool=False) -> Tuple[int, Counter]:
    words = list(tokenize_words(text))
    tokens = [lemmatize(w) for w in words] if use_lemma else words
    bag = Counter(tokens)
    per_key = Counter()

    # Подсчет одиночных слов как фраз из 1 токена и многословных фраз
    for original, norm in phrase_index:
        if ordered:
            # скользящее окно
            n = len(norm)
            if n == 1:
                per_key[original] += bag.get(norm[0], 0)
            else:
                for i in range(0, max(0, len(tokens) - n + 1)):
                    if tuple(tokens[i:i+n]) == norm:
                        per_key[original] += 1
        else:
            # неупорядоченные фразы: считаем вхождение, если все токены присутствуют
            if isinstance(norm, frozenset):
                # для одиночного слова — берем частоту слова
                if len(norm) == 1:
                    tok = next(iter(norm))
                    per_key[original] += bag.get(tok, 0)
                else:
                    # одно вхождение на предложение/текст, если все токены встречаются
                    if norm.issubset(bag.keys()):
                        per_key[original] += 1

    return sum(per_key.values()), per_key

def aggregate_by_date(df, phrase_index, use_lemma: bool, ordered: bool=False):
    # Ожидаем колонки: publish_date, text
    df = df.copy()
    df['date'] = pd.to_datetime(df['publish_date']).dt.date
    by_date = defaultdict(lambda: dict(total=0, texts=set(), rows=[]))
    top = Counter()

    for i, row in df.iterrows():
        hits_total, per_key = text_hits(row.get('text', ''), phrase_index, use_lemma, ordered)
        if hits_total > 0:
            d = row['date']
            by_date[d]['total'] += hits_total
            by_date[d]['texts'].add(i)
            by_date[d]['rows'].append(i)
            top.update(per_key)

    import pandas as pd
    out = pd.DataFrame({
        'date': list(by_date.keys()),
        'keywords_count': [v['total'] for v in by_date.values()],
        'texts_with_hits': [len(v['texts']) for v in by_date.values()],
        'row_indices': [', '.join(map(str, v['rows'])) for v in by_date.values()],
    }).sort_values('date')

    top_df = pd.DataFrame(sorted(top.items(), key=lambda x: x[1], reverse=True), columns=['keyword','count'])
    return out, top_df
