"""Pure functions shared by the pipeline scripts.

Everything here is deterministic and free of I/O, so it is unit-tested
directly against hand-computed fixtures (tests/python/test_draftlib.py) and
mirrored in R/functions.R where the R implementation needs the same logic.
"""
from __future__ import annotations

import math
import re
import unicodedata


def norm(name: str) -> str:
    """Collapse a player name to a cross-source comparison key.

    Sources disagree on diacritics (Dončić/Doncic), sharp-s (Pleiß/Pleiss),
    Turkish dotless i (Aşık/Asik), suffixes ("Jackson, Jr."/"Jackson Jr."),
    and hyphens vs spaces (Zhi-zhi/Zhizhi) — normalise all of it away.
    """
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.casefold().replace("ı", "i")
    name = re.sub(r"[\s,]+(jr|sr|ii|iii|iv)\.?$", "", name.strip())
    return re.sub(r"[^a-z0-9]", "", name)


def pava_decreasing(picks: list[int], means: dict[int, float],
                    weights: dict[int, float]) -> dict[int, float]:
    """Weighted isotonic regression, constrained non-increasing in pick.
    Pool-adjacent-violators on the negated series."""
    blocks: list[list] = []  # [neg_mean, weight, [picks]]
    for p in picks:
        blocks.append([-means[p], weights[p], [p]])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            b = blocks.pop()
            a = blocks.pop()
            w = a[1] + b[1]
            blocks.append([(a[0] * a[1] + b[0] * b[1]) / w, w, a[2] + b[2]])
    fit = {}
    for neg, _, ps in blocks:
        for p in ps:
            fit[p] = -neg
    return fit


def sample_sd(xs: list[float]) -> float:
    """Sample standard deviation (n-1), 0 for fewer than two values —
    matching R's sd() so the two implementations reconcile."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def peak3(season_effs: list[float]) -> float:
    """Best sum over three consecutive played seasons (chronological
    order); the whole career when it spans three seasons or fewer."""
    if not season_effs:
        return 0.0
    if len(season_effs) <= 3:
        return sum(season_effs)
    return max(sum(season_effs[i:i + 3])
               for i in range(len(season_effs) - 2))
