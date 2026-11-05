#!/usr/bin/env python3
"""Recompute the Part III numbers (Chapters 12 to 17) from the public Tonmick files.

    python -I verification/independent/details_check.py companion

Part III shows one detail changing one answer in each chapter. Every Tonmick
number it prints comes from the same public files as the spine study (the
Predictive companion's copy of Tonmick v1.0.0, anchor sample):

  Chapter 12  who joined: join rates by part-time and first-in-family status,
              and entry grades, for joiners and non-joiners (participants.csv)
  Chapter 13  the wellbeing and stress scales at entry: complete cases, the
              correlation between scale means, Cronbach's alpha for each scale,
              Spearman's correction for unreliability, and the paper-versus-online
              gap on stress item 2 (baseline.csv; wb4 and st4 reverse-keyed as
              6 minus the value, as DICTIONARY.csv says)
  Chapter 14  support visits: rates per month enrolled by offer, the rate ratio
              with a Poisson interval and p value, the Pearson dispersion, the
              same interval and p value allowing that extra variation
              (quasi-Poisson), the variance-to-mean ratio, and the share of zeros
              (registry.csv: visits_12, months_enrolled)
  Chapter 15  12-month grades, offered minus not offered, in each of the 16
              colleges, combined by inverse-variance weights with a
              DerSimonian-Laird between-college variance; the 95% interval for
              the average and the 95% prediction interval for a new college
              (t with 14 degrees of freedom); and the students with no 12-month
              grade, by group, with a check that each left before month 4 or
              withdrew consent
  Chapter 17  students not offered mentoring, sorted by entry grade: the bottom
              and top quarters, their distance from the group average at entry
              and in 12-month college grades, and the share of each quarter with
              no 12-month grade

Standard library only; it shares no code with the companion. Each value is
compared with what the book prints (EXPECTED). In the book's repository each phrase
in PHRASES must also appear in guide/guide.md; the public copy
(github.com/nicholaskarlson/facts) checks the values only. Prints
DETAILS_CHECK_OK values=N, with phrases=M where the book's text is checked.
"""
import csv, math, statistics as st, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANCHOR = Path("open-materials/predictive-reasoning-with-statistics/source/tonmick-v1.0.0/data/anchor")
Z975 = 1.959963984540054
T975_DF14 = 2.1447866879169273  # the 97.5th percentile of t with 14 degrees of freedom

EXPECTED = {
    # Chapter 12
    "join_pct_full_time": "80", "join_pct_part_time": "70",
    "join_pct_not_first_gen": "79", "join_pct_first_gen": "71",
    "entry_grade_joiners": "3.01", "entry_grade_non_joiners": "2.74",
    # Chapter 13
    "complete_items": "922", "scale_r": "-.36", "alpha_wb": ".78", "alpha_st": ".78",
    "corrected_r": "-.47", "st2_gap_paper": "0.46", "st2_gap_online": "0.02",
    # Chapter 14
    "visits_rate_ratio_pct": "13", "visits_p_poisson": ".0009",
    "visits_ci_poisson_pct": "5 22", "visits_dispersion": "3.3", "visits_var_mean": "3.6",
    "visits_p_quasi": ".07", "visits_ci_quasi_pct": "-1 29", "visits_zero_pct": "30",
    # Chapter 15
    "grade_n": "1116", "grade_colleges": "16", "grade_positive": "12",
    "grade_re_mean": "0.08", "grade_ci_low_above_zero": "True", "grade_ci_high": "0.16",
    "grade_pi": "-0.14 0.30",
    "grade_missing": "103", "grade_missing_pct_offered": "8", "grade_missing_pct_not": "9",
    "grade_at_exit": "124",   # gpa12 recorded on leaving (gpa_at_exit = 1), all after month 4
    "grade_at_exit_all_after_month_4": "True",
    "grade_missing_all_left_early": "True",
    # Chapter 17
    "rtm_quarter_n": "152", "rtm_bottom_entry": "0.58", "rtm_bottom_later": "0.49",
    "rtm_top_entry": "0.60", "rtm_top_later": "0.46",
    "rtm_bottom_missing_pct": "13", "rtm_top_missing_pct": "9",
}

PHRASES = [
    # Chapter 12
    "80% of full-time students joined, against 70% of part-time students",
    "79% against 71%",
    # Chapter 13
    "922 students who answered all ten items",
    "the correlation between the two scores is −.36",
    "about .78 for each scale",
    "about −.47",
    "almost half a point higher than the other stress items",
    # Chapter 14
    "about 13% more visits per month",
    "p = .0009",
    "from 5% to 22% more",
    "more than three times their average",
    "the same data give p = .07",
    "from about 1% fewer to 29% more",
    "30% of students made no visits at all",
    # Chapter 15
    "1,116 students with a recorded grade",
    "For 124 students who left after their first four months",
    "12 of the 16 colleges",
    "less than a tenth of a grade point",
    "from about −0.14 to +0.30 grade points",
    "Grades are missing for 103 students who left within their first four months or withdrew consent: 8% of the offered group and 9% of the others",
    # Chapter 17
    "152 students",
    "about six tenths of a grade point below",
    "about half a grade point below",
    "less than half a point above",
    "13% of the bottom quarter, against 9% of the top quarter",
]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def corr(x, y):
    mx, my = st.mean(x), st.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return num / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def alpha(rows):
    k = len(rows[0])
    total_var = st.variance([sum(r) for r in rows])
    return k / (k - 1) * (1 - sum(st.variance(c) for c in zip(*rows)) / total_var)


def pct0(x):
    return f"{x * 100:.0f}"


def dot2(x):
    """A correlation or reliability as printed: two decimals, no leading zero."""
    s = f"{x:.2f}"
    return s.replace("0.", ".", 1)


def analyze(companion):
    a = companion / ANCHOR
    part = {r["student_id"]: r for r in read(a / "participants.csv")}
    base = {r["student_id"]: r for r in read(a / "baseline.csv")}
    reg = {r["student_id"]: r for r in read(a / "registry.csv")}
    out, extra = {}, {}

    # Chapter 12: who joined
    def join_rate(var, val):
        ids = [s for s in part if part[s][var] == val]
        return sum(part[s]["responded_baseline"] == "1" for s in ids) / len(ids)
    out["join_pct_full_time"] = pct0(join_rate("part_time", "0"))
    out["join_pct_part_time"] = pct0(join_rate("part_time", "1"))
    out["join_pct_not_first_gen"] = pct0(join_rate("first_gen", "0"))
    out["join_pct_first_gen"] = pct0(join_rate("first_gen", "1"))
    joined = [s for s in part if part[s]["responded_baseline"] == "1"]
    not_joined = [s for s in part if part[s]["responded_baseline"] == "0"]
    out["entry_grade_joiners"] = f"{st.mean(float(part[s]['prior_grade']) for s in joined):.2f}"
    out["entry_grade_non_joiners"] = f"{st.mean(float(part[s]['prior_grade']) for s in not_joined):.2f}"
    extra["join"] = {k: float(out[k]) for k in ("join_pct_full_time", "join_pct_part_time",
                                                "join_pct_not_first_gen", "join_pct_first_gen")}

    # Chapter 13: two scales at entry
    items = [f"{p}{i}" for p in ("wb", "st") for i in range(1, 6)]
    complete = [s for s in base if all(base[s][c] != "" for c in items)]
    wb_rows, st_rows = [], []
    for s in complete:
        wb = [int(base[s][f"wb{i}"]) for i in range(1, 6)]
        sr = [int(base[s][f"st{i}"]) for i in range(1, 6)]
        wb[3], sr[3] = 6 - wb[3], 6 - sr[3]
        wb_rows.append(wb)
        st_rows.append(sr)
    r = corr([st.mean(x) for x in wb_rows], [st.mean(x) for x in st_rows])
    aw, at = alpha(wb_rows), alpha(st_rows)
    corrected = r / math.sqrt(aw * at)
    gaps = {"paper": [], "online": []}
    for s, sr in zip(complete, st_rows):
        gaps[base[s]["mode"]].append(sr[1] - st.mean([sr[0], sr[2], sr[3], sr[4]]))
    out.update({"complete_items": str(len(complete)), "scale_r": dot2(r), "alpha_wb": dot2(aw),
                "alpha_st": dot2(at), "corrected_r": dot2(corrected),
                "st2_gap_paper": f"{st.mean(gaps['paper']):.2f}", "st2_gap_online": f"{st.mean(gaps['online']):.2f}"})
    extra["measure"] = {"observed": r, "corrected": corrected}

    # Chapter 14: support visits by offer
    grp = {o: [s for s in base if base[s]["offer"] == o] for o in "10"}
    visits = {o: sum(int(reg[s]["visits_12"]) for s in grp[o]) for o in "10"}
    months = {o: sum(float(reg[s]["months_enrolled"]) for s in grp[o]) for o in "10"}
    rate = {o: visits[o] / months[o] for o in "10"}
    rr = rate["1"] / rate["0"]
    se = math.sqrt(1 / visits["1"] + 1 / visits["0"])
    p_pois = 2 * normal_cdf(-abs(math.log(rr)) / se)
    pearson = sum((int(reg[s]["visits_12"]) - rate[o] * float(reg[s]["months_enrolled"])) ** 2
                  / (rate[o] * float(reg[s]["months_enrolled"])) for o in "10" for s in grp[o])
    phi = pearson / (len(base) - 2)
    se_q = se * math.sqrt(phi)
    p_quasi = 2 * normal_cdf(-abs(math.log(rr)) / se_q)
    ci = lambda s_: (math.exp(math.log(rr) - Z975 * s_) - 1, math.exp(math.log(rr) + Z975 * s_) - 1)
    lo, hi = ci(se)
    lq, hq = ci(se_q)
    allv = [int(reg[s]["visits_12"]) for s in base]
    out.update({"visits_rate_ratio_pct": pct0(rr - 1), "visits_p_poisson": f"{p_pois:.4f}".lstrip("0"),
                "visits_ci_poisson_pct": f"{pct0(lo)} {pct0(hi)}", "visits_dispersion": f"{phi:.1f}",
                "visits_var_mean": f"{st.variance(allv) / st.mean(allv):.1f}",
                "visits_p_quasi": f"{p_quasi:.2f}".lstrip("0"), "visits_ci_quasi_pct": f"{pct0(lq)} {pct0(hq)}",
                "visits_zero_pct": pct0(sum(v == 0 for v in allv) / len(allv))})
    extra["visits"] = {"rr": rr, "poisson": (rr * math.exp(-Z975 * se), rr * math.exp(Z975 * se)),
                       "quasi": (rr * math.exp(-Z975 * se_q), rr * math.exp(Z975 * se_q))}

    # Chapter 15: 16 colleges combined
    with_grade = [s for s in base if reg[s]["gpa12"] != ""]
    by = defaultdict(lambda: {"1": [], "0": []})
    for s in with_grade:
        by[base[s]["college_id"]][base[s]["offer"]].append(float(reg[s]["gpa12"]))
    colleges, est, var = sorted(by), [], []
    for c in colleges:
        g1, g0 = by[c]["1"], by[c]["0"]
        est.append(st.mean(g1) - st.mean(g0))
        var.append(st.variance(g1) / len(g1) + st.variance(g0) / len(g0))
    w = [1 / v for v in var]
    fe = sum(wi * e for wi, e in zip(w, est)) / sum(w)
    q = sum(wi * (e - fe) ** 2 for wi, e in zip(w, est))
    c_ = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (q - (len(est) - 1)) / c_)
    wr = [1 / (v + tau2) for v in var]
    re = sum(wi * e for wi, e in zip(wr, est)) / sum(wr)
    se_re = math.sqrt(1 / sum(wr))
    half_pi = T975_DF14 * math.sqrt(tau2 + se_re ** 2)
    missing = [s for s in base if reg[s]["gpa12"] == ""]
    left_early = all(reg[s]["exit_type"] == "consent_withdrawn"
                     or (reg[s]["exit_type"] != "none" and float(reg[s]["exit_month"]) < 4) for s in missing)
    miss_by = {z: sum(base[s]["offer"] == z for s in missing) / sum(base[s]["offer"] == z for s in base) for z in "10"}
    at_exit = [s for s in base if reg[s]["gpa12"] != "" and reg[s]["gpa_at_exit"] == "1"]
    out["grade_at_exit"] = str(len(at_exit))
    out["grade_at_exit_all_after_month_4"] = str(all(float(reg[s]["exit_month"]) >= 4 for s in at_exit))
    out.update({"grade_missing": str(len(missing)), "grade_missing_pct_offered": pct0(miss_by["1"]),
                "grade_missing_pct_not": pct0(miss_by["0"]), "grade_missing_all_left_early": str(left_early)})
    out.update({"grade_n": str(len(with_grade)), "grade_colleges": str(len(colleges)),
                "grade_positive": str(sum(e > 0 for e in est)), "grade_re_mean": f"{re:.2f}",
                "grade_ci_low_above_zero": str(re - Z975 * se_re > 0), "grade_ci_high": f"{re + Z975 * se_re:.2f}",
                "grade_pi": f"{re - half_pi:.2f} {re + half_pi:.2f}"})
    extra["colleges"] = {"est": est, "se": [math.sqrt(v) for v in var], "re": re,
                         "ci": (re - Z975 * se_re, re + Z975 * se_re), "pi": (re - half_pi, re + half_pi)}

    # Chapter 17: entry grades and 12-month grades, students not offered mentoring
    ctrl = sorted((s for s in base if base[s]["offer"] == "0"), key=lambda s: (float(part[s]["prior_grade"]), s))
    quarter = len(ctrl) // 4
    bottom, top = ctrl[:quarter], ctrl[-quarter:]
    known = [s for s in ctrl if reg[s]["gpa12"] != ""]
    m_entry = st.mean(float(part[s]["prior_grade"]) for s in known)
    m_later = st.mean(float(reg[s]["gpa12"]) for s in known)

    def gaps_for(g):
        gk = [s for s in g if reg[s]["gpa12"] != ""]
        entry = st.mean(float(part[s]["prior_grade"]) for s in gk) - m_entry
        later = st.mean(float(reg[s]["gpa12"]) for s in gk) - m_later
        return entry, later, 1 - len(gk) / len(g)
    be, bl, bm = gaps_for(bottom)
    te, tl, tm = gaps_for(top)
    out.update({"rtm_quarter_n": str(quarter), "rtm_bottom_entry": f"{-be:.2f}", "rtm_bottom_later": f"{-bl:.2f}",
                "rtm_top_entry": f"{te:.2f}", "rtm_top_later": f"{tl:.2f}",
                "rtm_bottom_missing_pct": pct0(bm), "rtm_top_missing_pct": pct0(tm)})
    extra["rtm"] = {"bottom": (be, bl), "top": (te, tl)}
    return out, extra


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    got, _ = analyze(Path(sys.argv[1]))
    problems = [f"{k}: the files give {got.get(k)}, the book prints {v}" for k, v in EXPECTED.items() if got.get(k) != v]
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
        print("DETAILS_CHECK_FAILED")
        sys.exit(1)
    print(f"DETAILS_CHECK_OK values={len(EXPECTED)}{shown}")


if __name__ == "__main__":
    main()
