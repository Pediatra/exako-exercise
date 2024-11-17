from difflib import SequenceMatcher
from math import ceil

from exako.core.helper import normalize_array_text, normalize_text

WORDS_PER_MINUTE = 40


def text_distance(s1, s2):
    s1 = normalize_text(s1)
    s2 = normalize_text(s2)

    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[m][n]


def text_diff(s1: str, s2: str) -> list[int]:
    s1_words = normalize_array_text(s1.split())
    s2_words = normalize_array_text(s2.split())

    diff_indexes = set()

    matcher = SequenceMatcher(None, s1_words, s2_words)

    all_indices = set(range(len(s2_words)))
    matching_blocks = set()

    for block in matcher.get_matching_blocks():
        _, j, size = block
        if size > 0:
            for idx in range(j, j + size):
                matching_blocks.add(idx)

    diff_indexes = all_indices - matching_blocks

    return list(diff_indexes)


def text_speak_time(text):
    text = normalize_text(text)

    words = text.split()
    total_words = len(words)

    words_per_second = WORDS_PER_MINUTE / 60
    return ceil(total_words / words_per_second)
