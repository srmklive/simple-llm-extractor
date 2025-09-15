
from collections import Counter
import re
from typing import List

# A compact English stopword list (good enough for a timeboxed prototype)
STOPWORDS = set('''a about above after again against all am an and any are aren't as at be because been before being below
between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had
hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm
i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only or other ought
our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs
them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was
wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't
would wouldn't you you'd you'll you're you've your yours yourself yourselves'''.split())

# Fallback noun-ish morphology heuristic
NOUN_SUFFIXES = ("tion","sion","ment","ness","ity","ship","ance","ence","er","or","ist","ism","acy")

def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z\-']+", text)

def is_probable_noun(word: str, prev_token: str | None) -> bool:
    w = word.lower()
    if w in STOPWORDS or len(w) <= 2:
        return False
    # Capitalized (not sentence-start) heuristic
    if word[0].isupper() and (prev_token is not None):
        return True
    # Morphology heuristic
    if w.endswith(NOUN_SUFFIXES):
        return True
    # Treat multi-hyphen words as nouns (e.g., "machine-learning")
    if "-" in w:
        return True
    return False

def extract_keywords(text: str, top_k: int = 3) -> List[str]:
    tokens = tokenize(text)
    counts = Counter()
    prev = None
    for t in tokens:
        if is_probable_noun(t, prev):
            counts[t.lower()] += 1
        prev = t
    if not counts:
        # Fallback: top non-stopword tokens by frequency
        fallback = Counter([t.lower() for t in tokens if t.lower() not in STOPWORDS])
        return [w for w,_ in fallback.most_common(top_k)]
    return [w for w,_ in counts.most_common(top_k)]
