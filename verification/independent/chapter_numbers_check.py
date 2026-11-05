#!/usr/bin/env python3
"""Recompute the numbers the book works out for itself, outside the spine study.

    python -I verification/independent/chapter_numbers_check.py [companion]

Chapter 2 prints a few numbers that need no data: chances for a fair coin, the
shared-birthday chance for 23 people, and an invented screening example.
Chapter 20 prints an invented example of two beliefs converging: Maya starts
from Beta(8, 2) and Sam from Beta(5, 5) for the share of matched pairs in which
the app student wins; after 11 wins in 20 pairs, and 110 in 200, each posterior
mean is (a + wins) / (a + b + pairs). The Try it here exercises (Chapters 5 to
10) use small invented numbers, and their worked answers in the back matter
print what follows from them: 20 studies at the 5% standard, a survey that
missed most of those who withdrew, a difference against its spread, a p value
read off an interval, and a risk score's catch rate, hit rate, and accuracy. This
script recomputes them exactly (fractions and integers, standard library only),
compares each with what the book prints (EXPECTED), and, in the book's repository,
checks that each phrase in PHRASES appears in guide/guide.md (the public copy,
github.com/nicholaskarlson/facts, checks the values only). The companion argument is accepted, and
ignored, so that run_independent.sh can call every script the same way.
Prints CHAPTER_NUMBERS_OK values=N, with phrases=M where the book's text is checked.
"""
import math
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    "coin_7_of_10_pct": "17",                 # 176/1024, printed "about 17%"
    "coin_7_of_10_one_in": "6",               # "about one try in six"
    "coin_700_of_1000_below_1e-24": "True",   # "less than one in a trillion trillion"
    "coin_45_to_55_of_1000_above_99pct": "True",  # "nearly every result lies between 45% and 55%"
    "birthday_23_above_half": "True",         # "a little better than one half"
    "birthday_23_pct": "51",
    "screen_have": "10",
    "screen_true_flags": "9",
    "screen_without": "990",
    "screen_false_flags": "99",
    "screen_flagged": "108",
    # Chapter 20
    "maya_start": "80", "sam_start": "50", "gap_start": "30",
    "maya_20": "63", "sam_20": "53", "gap_20": "10",
    "maya_200": "56", "sam_200": "55", "gap_200_below_2": "True",
    # Try it here (invented numbers; worked answers in the back matter)
    "ex5_expected_significant": "1", "ex5_at_least_one_pct": "64",
    "ex6_respondents_pct": "9", "ex6_all_pct": "15", "ex6_nonrespondents": "48 200", "ex6_nonrespondents_pct": "24",
    "ex7_share_of_spread": "2/5",
    "ex8_p_from_interval": ".40",
    "ex10_caught_pct": "60", "ex10_missed": "40", "ex10_flags_right_pct": "30", "ex10_flagged_stayed_in_10": "7",
    "ex10_accuracy_pct": "82", "ex10_flag_nobody_pct": "90", "ex10_withdrew_in_10": "1",
}

PHRASES = [
    "7 or more heads in 10 tosses about 17% of the time, or about one try in six",
    "700 or more heads in 1,000 tosses with a chance of less than one in a trillion trillion",
    "nearly every result lies between 45% and 55% heads",
    "In a room of 23 people, the chance that two of them share a birthday is a little better than one half",
    "About 10 have the condition, and the test flags 9 of them",
    "Of the 990 who do not have it, the test wrongly flags about 99",
    "So of the 108 people flagged, only 9 have the condition",
    "Maya believes the app student will win about 80% of the time",
    "Sam believes it will be about 50%",
    "In the first 20 pairs, the app student wins 11",
    "Maya's best estimate falls to about 63%. Sam's rises to about 53%",
    "They began 30 points apart, and now they are 10 points apart",
    "The study continues to 200 pairs, and the app student wins 110",
    "Now Maya's estimate is about 56%, Sam's about 55%, and they are less than 2 points apart",
    # Try it here, and the worked answers
    "A lab runs 20 small studies", "with p = .03", "5% of 20 is 1",
    "The chance that at least one of the 20 comes out significant is about 64%",
    "The 9% is 27 of the 300 students who answered a year-end survey",
    "its records show that 75 of them withdrew", "75 of 500, or 15%", "48 of 200, or 24%",
    "the quiz section averaged 74 on the final exam and the other section 70",
    "a 95% interval from 1 to 7 points", "about 10 points from their section's average",
    "About two fifths of the usual spread",
    "(p = .40)", "3 points better with the program, with a 95% interval from 4 points worse to 10 points better",
    "flags 200 of its 1,000 first-year students",
    "Of the 200 flagged, 60 later withdraw. Of the 800 not flagged, 40 withdraw",
    "60 of the 100 who withdrew, or 60%", "The score missed 40 of them", "60 of 200, or 30%",
    "Seven in ten flagged students would have stayed anyway", "82% accurate",
    "right about the 900 students who stayed: 90% accurate", "When only 1 student in 10 withdraws",
]

BELIEFS = {"maya": (8, 2), "sam": (5, 5)}   # Chapter 20: Beta(a, b) starting beliefs
EVIDENCE = [(0, 0), (11, 20), (110, 200)]   # wins, pairs


def tail(n, k):
    """P(X >= k) for X ~ Binomial(n, 1/2), exactly."""
    return Fraction(sum(comb(n, j) for j in range(k, n + 1)), 2 ** n)


def between(n, lo, hi):
    return Fraction(sum(comb(n, j) for j in range(lo, hi + 1)), 2 ** n)


def analyze():
    p7 = tail(10, 7)
    no_shared = Fraction(1)
    for i in range(23):
        no_shared *= Fraction(365 - i, 365)
    shared = 1 - no_shared
    people, rate, accuracy = 1000, Fraction(1, 100), Fraction(9, 10)
    have = people * rate
    without = people - have
    true_flags, false_flags = have * accuracy, without * (1 - accuracy)
    post = {who: [Fraction(a + w, a + b + n) for w, n in EVIDENCE] for who, (a, b) in BELIEFS.items()}
    return {
        "maya_start": f"{float(post['maya'][0]) * 100:.0f}", "sam_start": f"{float(post['sam'][0]) * 100:.0f}",
        "gap_start": f"{float(post['maya'][0] - post['sam'][0]) * 100:.0f}",
        "maya_20": f"{float(post['maya'][1]) * 100:.0f}", "sam_20": f"{float(post['sam'][1]) * 100:.0f}",
        "gap_20": f"{float(post['maya'][1] - post['sam'][1]) * 100:.0f}",
        "maya_200": f"{float(post['maya'][2]) * 100:.0f}", "sam_200": f"{float(post['sam'][2]) * 100:.0f}",
        "gap_200_below_2": str(post['maya'][2] - post['sam'][2] < Fraction(2, 100)),
        "coin_7_of_10_pct": f"{float(p7) * 100:.0f}",
        "coin_7_of_10_one_in": f"{float(1 / p7):.0f}",
        "coin_700_of_1000_below_1e-24": str(tail(1000, 700) < Fraction(1, 10 ** 24)),
        "coin_45_to_55_of_1000_above_99pct": str(between(1000, 450, 550) > Fraction(99, 100)),
        "birthday_23_above_half": str(shared > Fraction(1, 2)),
        "birthday_23_pct": f"{float(shared) * 100:.0f}",
        "screen_have": f"{float(have):.0f}",
        "screen_true_flags": f"{float(true_flags):.0f}",
        "screen_without": f"{float(without):.0f}",
        "screen_false_flags": f"{float(false_flags):.0f}",
        "screen_flagged": f"{float(true_flags + false_flags):.0f}",
        **exercises(),
    }


def exercises():
    """The Try it here numbers, exactly where they are exact."""
    studies, alpha = 20, Fraction(5, 100)
    resp_n, resp_w, all_n, all_w = 300, 27, 500, 75
    diff, spread = 4, 10
    est, lo, hi = 3, -4, 10                       # points, with a 95% interval
    se = (hi - lo) / 2 / 1.959963984540054
    p_two = 1 + math.erf(-est / se / math.sqrt(2))  # 2 * P(Z < -est / se)
    flagged, flagged_w, unflagged, unflagged_w = 200, 60, 800, 40
    withdrew = flagged_w + unflagged_w
    total = flagged + unflagged
    correct = flagged_w + (unflagged - unflagged_w)
    pct = lambda fr: f"{float(fr) * 100:.0f}"
    return {
        "ex5_expected_significant": f"{studies * alpha}",
        "ex5_at_least_one_pct": pct(1 - (1 - alpha) ** studies),
        "ex6_respondents_pct": pct(Fraction(resp_w, resp_n)),
        "ex6_all_pct": pct(Fraction(all_w, all_n)),
        "ex6_nonrespondents": f"{all_w - resp_w} {all_n - resp_n}",
        "ex6_nonrespondents_pct": pct(Fraction(all_w - resp_w, all_n - resp_n)),
        "ex7_share_of_spread": str(Fraction(diff, spread)),
        "ex8_p_from_interval": f"{p_two:.2f}".lstrip("0"),
        "ex10_caught_pct": pct(Fraction(flagged_w, withdrew)),
        "ex10_missed": str(unflagged_w),
        "ex10_flags_right_pct": pct(Fraction(flagged_w, flagged)),
        "ex10_flagged_stayed_in_10": f"{float(Fraction(flagged - flagged_w, flagged)) * 10:.0f}",
        "ex10_accuracy_pct": pct(Fraction(correct, total)),
        "ex10_flag_nobody_pct": pct(Fraction(total - withdrew, total)),
        "ex10_withdrew_in_10": f"{float(Fraction(withdrew, total)) * 10:.0f}",
    }


def main():
    problems = []
    got = analyze()
    for k, want in EXPECTED.items():
        if got.get(k) != want:
            problems.append(f"{k}: computed {got.get(k)}, the book prints {want}")
    # The book's repository (it has guide.env) must hold the text, and every phrase must be in it.
    # The public copy (github.com/nicholaskarlson/facts) holds no book text, so it checks the values only.
    guide = ROOT / "guide/guide.md"
    shown = ""
    if guide.is_file():
        text = guide.read_text(encoding="utf-8")
        problems += [f"phrase not in guide/guide.md: {ph!r}" for ph in PHRASES if ph not in text]
        shown = f" phrases={len(PHRASES)}"
    elif (ROOT / "guide.env").is_file():
        problems.append("guide/guide.md is missing")
    if problems:
        print("\n".join(problems))
        print("CHAPTER_NUMBERS_FAILED")
        sys.exit(1)
    print(f"CHAPTER_NUMBERS_OK values={len(EXPECTED)}{shown}")


if __name__ == "__main__":
    main()
