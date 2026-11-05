#!/usr/bin/env python3
"""Recompute the spine study's numbers from the public Tonmick files.

    python -I verification/independent/spine_check.py companion

The spine study is the Tonmick mentoring study: 1,600 students were invited,
1,219 joined, and those who joined were randomized to an offer of mentoring or
no offer. The outcome is withdrawal within the first year. The files are the
Predictive companion's public copies of Tonmick v1.0.0 (anchor sample) and of
the v1.1.0 observed registry, which adds outcomes for the invited students who
did not join.

The book compares the groups on known outcomes, as Book 7 (Unit 7) and the
Predictive guide do: the 11 students who withdrew consent (4 offered, 7 not)
have no outcome after that point, so they are left out of the rates. Chapter 6
also prints the rates that count them as staying (13.1% and 15.2%).

Standard library only. Counts and proportions are exact fractions; the standard
error, the interval, and the posterior probabilities use floating point. The
posterior probabilities in Chapter 3 start from a flat prior on each group's
withdrawal rate (Beta(1, 1)) and integrate the two Beta posteriors on a fine
grid; the result is stable to well beyond the printed digits. Chapter 8 compares
two starting points with a normal approximation to the difference: an open-minded
one (a flat prior on the difference) and a skeptical one (normal, centered on no
effect, standard deviation 1 point, so 95% of it lies within about 2 points of
zero). Chapter 8 also prints the two-sided p value and, for a true reduction of
2 points from the not-offered group's rate, the power of a trial this size and the
sample size per group for 80% power (two-sided test at the 5% level, normal
approximation, unpooled variances). The power is for a stated effect worth
detecting, not for the estimate the trial happened to find. Chapter 3 prints the
number of joiners who transferred out of the system before any withdrawal; they
count as not withdrawn, as withdrawn_12 defines it. Chapter 6 prints
the not-offered group's rates by part-time status, the design-weighted part-time
share of all invited students (base_weight in participants.csv, an estimate of
the colleges' mix), the two rates recombined in that mix, and a Wilson 95%
interval for 93 of 603. Chapter 18 works the mentoring decision through with
invented costs (COST_PER_STUDENT and VALUE_AVOIDED below): the break-even effect,
the chance that the offer clears it from each starting point (the normal
posteriors above), the expected withdrawals avoided and the expected net value
for every 1,000 students offered, the same chances at a higher value
(VALUE_AVOIDED_HIGH), and the 95% margin of a trial with 4,800 students a group.
Every value is compared with what the
book prints (EXPECTED). In the book's repository, every phrase in PHRASES must
also appear in guide/guide.md, so the text and the files cannot drift apart; the
public copy (github.com/nicholaskarlson/facts) holds no book text and checks the
values only. Exits non-zero on any mismatch. Prints SPINE_CHECK_OK values=N, with
phrases=M where the book's text is checked.
"""
import csv, math, sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUB = Path("open-materials/predictive-reasoning-with-statistics/source")
ANCHOR = SUB / "tonmick-v1.0.0/data/anchor"
OBSERVED = SUB / "tonmick-observed-v1.1.0/data/anchor_observed_registry.csv"
Z975 = 1.959963984540054  # the 97.5th percentile of the standard normal
GRID = 200_000            # grid points on (0, 0.5) for the posterior integrals
# Chapter 18's decision: invented costs, stated in the text as invented.
COST_PER_STUDENT = 200        # dollars for each student offered mentoring
VALUE_AVOIDED = 10_000        # dollars a college puts on each withdrawal avoided
VALUE_AVOIDED_HIGH = 20_000   # the same, also counting what the student gains
LARGER_TRIAL_PER_GROUP = 4_800

# What the book prints, as printed (percentages and points to the stated digits).
EXPECTED = {
    "invited": "1600",
    "colleges": "16",
    "joined": "1219",
    "offered": "609",
    "not_offered": "610",
    "consent_withdrawn": "11",
    "consent_withdrawn_offered": "4",
    "consent_withdrawn_not_offered": "7",
    "offered_known": "605",
    "not_offered_known": "603",
    "withdrew_offered": "80",
    "withdrew_not_offered": "93",
    "pct_offered_known": "13",            # printed as "13%"
    "pct_not_offered_known": "15",        # printed as "15%"
    "pct_offered_known_1dp": "13.2",
    "pct_not_offered_known_1dp": "15.4",
    "pct_offered_all_1dp": "13.1",        # Chapter 6: consent withdrawals counted as staying
    "pct_not_offered_all_1dp": "15.2",
    "uptake": "363",                      # attended at least 3 of 6 sessions
    "transferred_first": "43",            # Chapter 3: transferred out before any withdrawal
    "uptake_in_10": "6",                  # "about 6 in 10"
    "difference_points": "-2.2",
    "se_points": "2.01",
    "ci_low_points": "-6.1",
    "ci_high_points": "1.7",
    "did_not_join": "381",
    "withdrew_did_not_join": "84",
    "pct_did_not_join": "22",             # printed as "22%"
    "pct_did_not_join_1dp": "22.0",
    "pct_all_invited_no_offer": "17",     # printed as "about 17%"
    "prob_offer_lowered": "86",           # flat prior, printed as "about 86%"
    "prob_lowered_2_points": "54",        # flat prior, printed as "about 54%"
    # Chapter 6
    "pt_not_offered_known": "214",
    "withdrew_pt": "48",
    "pct_pt": "22",
    "ft_not_offered_known": "389",
    "withdrew_ft": "45",
    "pct_ft": "12",
    "pct_pt_in_group": "35",              # "about 35% of the students in this group"
    "pt_share_weighted_pct": "25",        # "about a quarter"
    "pct_recombined": "14",               # "about 14%"
    "wilson_low_pct": "13",               # "from about 13% to 19%"
    "wilson_high_pct": "19",
    # Chapter 8
    "p_two_sided": ".27",
    "power_pct_2_points": "17",           # for a true 2-point reduction
    "power_one_in": "6",                  # "about 1 time in 6"
    "n_per_group_80_hundreds": "4,800",   # "about 4,800 students in each group"
    "times_each_group": "8",              # "about eight times as many as each group had"
    "prob_offer_lowered_normal": "86",
    "prob_offer_lowered_skeptic": "69",   # "about 69%"
    "prob_lowered_2_points_skeptic": "4", # "about 4%"
    # Chapter 18: the decision
    "breakeven_points": "2",
    "pays_open_pct": "54",
    "pays_skeptic_pct": "4",
    "avoided_open_per_1000": "22",
    "value_open_per_1000": "220,000",
    "net_open_per_1000": "20,000",
    "avoided_skeptic_per_1000": "4",
    "net_skeptic_per_1000": "-157,000",
    "trial_per_1000_fewer_more": "61 17",
    "breakeven_points_high": "1",
    "pays_open_high_pct": "72",
    "pays_skeptic_high_pct": "26",
    "larger_trial_margin_points": "1.4",
    "larger_trial_interval_at_estimate": "0.8 3.6",   # "from about 0.8 to 3.6 points"
}

# Phrases the book prints from these numbers. Each must appear in guide/guide.md.
# Add one here whenever a chapter prints a spine number.
PHRASES = [
    "1,600 first-year students at 16 Tonmick colleges",
    "Of these, 1,219 joined",
    "Eleven students later withdrew their consent",
    "as 43 of those who joined did, counts as not having withdrawn",
    "| Offered mentoring | 605 | 80 (13%) |",
    "| Not offered | 603 | 93 (15%) |",
    "93 of 603",
    "13% against 15%",
    "a difference of 2.2 percentage points",
    "About 6 in 10 students who were offered mentoring attended at least three sessions",
    "lowered withdrawal by 2.2 points",
    "from 6.1 points fewer withdrawals to 1.7 points more",
    "the 381 invited students who did not join",
    "84 of them withdrew within the year, or 22%",
    "about 17% of all 1,600 invited students",
    "about 86%",
    "about 54%",
    # Chapter 6
    "93 of 610, or 15.2%",
    "93 of 603, or 15.4%",
    "48 of 214 part-time students (22%), against 45 of 389 full-time students (12%)",
    "about 35% of the students in this group are part-time",
    "about a quarter of first-year students are part-time",
    "an overall rate of about 14%",
    "with a 95% interval from about 13% to 19%",
    # Chapter 8
    "gives p = .27",
    "Suppose the offer really lowered withdrawal by 2 points",
    "only about 1 time in 6",
    "about 4,800 students in each group, about eight times as many as each group had",
    "a chance of about 69% that the offer lowered withdrawal",
    "falls from about 54% to about 4%",
    # Chapter 18
    "Suppose the offer costs $200 for each student offered, and the colleges value each withdrawal avoided at $10,000",
    "avoids at least 2 withdrawals for every 100 students offered, a drop of 2 points",
    "From an open starting point, the chance that the offer lowered withdrawal by 2 points or more is about 54%",
    "From the skeptical starting point of Chapter 8, it is about 4%",
    "about 22 withdrawals avoided, worth about $220,000, against a cost of $200,000",
    "an expected gain of about $20,000",
    "about 4 withdrawals avoided, and an expected loss of about $157,000",
    "from 61 fewer withdrawals to 17 more for every 1,000 students offered",
    "might put it at $20,000. Then the break-even effect falls to 1 point",
    "about 72% from the open start and about 26% from the skeptical one",
    "about 1.4 points either way",
    "If the larger trial also found 2.2 points, its interval would run from about 0.8 to 3.6 points",
    # Chapter 3's Try it here, and its worked answer
    "Among the 381 invited students who did not join the study, 22% withdrew within the year",
    "(84 of 381)",
    "the gap between 15% and 22%",
    "the chance that the offer lowered withdrawal is about 86%; from the skeptical one, about 69%",
]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pct(fr, digits=1):
    return f"{float(fr) * 100:.{digits}f}"


def posterior_probs(w1, n1, w0, n0, shift=Fraction(2, 100)):
    """P(p1 < p0) and P(p1 < p0 - shift) under flat priors: Beta(1 + w, 1 + n - w)."""
    a1, b1, a0, b0 = 1 + w1, 1 + n1 - w1, 1 + w0, 1 + n0 - w0
    lb1 = math.lgamma(a1) + math.lgamma(b1) - math.lgamma(a1 + b1)
    lb0 = math.lgamma(a0) + math.lgamma(b0) - math.lgamma(a0 + b0)
    h = 0.5 / GRID
    xs = [(i + 0.5) * h for i in range(GRID)]
    f1 = [math.exp((a1 - 1) * math.log(x) + (b1 - 1) * math.log1p(-x) - lb1) for x in xs]
    f0 = [math.exp((a0 - 1) * math.log(x) + (b0 - 1) * math.log1p(-x) - lb0) for x in xs]
    cdf1 = [0.0] * (GRID + 1)
    for i in range(GRID):
        cdf1[i + 1] = cdf1[i] + f1[i] * h
    k = round(float(shift) / h)
    lower = sum(f0[i] * (cdf1[i] + f1[i] * h / 2) for i in range(GRID)) * h
    lower_by = sum(f0[i] * cdf1[i - k] for i in range(k, GRID)) * h
    return lower, lower_by


def wilson(x, n, z=Z975):
    p = x / n
    centre, half = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / (1 + z * z / n), (centre + half) / (1 + z * z / n)


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_posterior(est, se, prior_sd=None):
    """Posterior mean and sd for a difference, normal likelihood; flat prior if prior_sd is None."""
    if prior_sd is None:
        return est, se
    prec = 1 / se ** 2 + 1 / prior_sd ** 2
    return (est / se ** 2) / prec, math.sqrt(1 / prec)


def analyze(companion, problems):
    base = {r["student_id"]: r for r in read(companion / ANCHOR / "baseline.csv")}
    reg = {r["student_id"]: r for r in read(companion / ANCHOR / "registry.csv")}
    part = read(companion / ANCHOR / "participants.csv")
    parts = {r["student_id"]: r for r in part}
    obs = read(companion / OBSERVED)
    if set(base) != set(reg):
        problems.append("baseline.csv and registry.csv list different students")
    arms = {"1": [0, 0, 0], "0": [0, 0, 0]}          # n, withdrew, consent withdrawn
    uptake = transferred = 0
    for sid, b in base.items():
        r = reg[sid]
        a = arms[b["offer"]]
        a[0] += 1
        a[1] += r["exit_type"] == "withdrawal"
        a[2] += r["exit_type"] == "consent_withdrawn"
        transferred += r["exit_type"] == "transfer"
        if r["exit_type"] == "transfer" and r["withdrawn_12"] != "0":
            problems.append(f"{sid}: a transfer counted as a withdrawal")
        uptake += b["offer"] == "1" and b["uptake"] == "1"
        if b["offer"] == "0" and b["uptake"] != "0":
            problems.append(f"{sid}: uptake without an offer")
        if (r["exit_type"] == "withdrawal") != (r["withdrawn_12"] == "1"):
            problems.append(f"{sid}: exit_type and withdrawn_12 disagree")
    n1, w1, c1 = arms["1"]
    n0, w0, c0 = arms["0"]
    k1, k0 = n1 - c1, n0 - c0                          # known outcomes
    p1, p0 = Fraction(w1, k1), Fraction(w0, k0)
    diff = p1 - p0
    se = math.sqrt(float(p1 * (1 - p1) / k1 + p0 * (1 - p0) / k0))
    lo, hi = float(diff) - Z975 * se, float(diff) + Z975 * se
    # The v1.1.0 observed registry: the same outcomes for those who joined, plus the 381 who did not.
    nonresp = [r for r in obs if r["responded_baseline"] == "0"]
    for r in obs:
        if r["responded_baseline"] == "1":
            b, g = base.get(r["student_id"]), reg.get(r["student_id"])
            if b is None or b["offer"] != r["offer"]:
                problems.append(f"{r['student_id']}: offer differs between v1.0.0 and the v1.1.0 registry")
            elif r["outcome_known"] == "1" and (r["withdrawal_label"] == "1") != (g["exit_type"] == "withdrawal"):
                problems.append(f"{r['student_id']}: withdrawal differs between v1.0.0 and the v1.1.0 registry")
    if any(r["outcome_known"] != "1" for r in nonresp):
        problems.append("some invited students who did not join have no known outcome")
    wn = sum(r["withdrawal_label"] == "1" for r in nonresp)
    # Everyone invited, with no offer: the randomized no-offer rate stands for all who joined.
    all_invited = (len(base) * p0 + wn) / len(part)
    lower, lower_by = posterior_probs(w1, k1, w0, k0)
    # Chapter 6: the not-offered group by part-time status, and the colleges' mix
    pt = {"1": [0, 0], "0": [0, 0]}
    for sid, b in base.items():
        r = reg[sid]
        if b["offer"] == "0" and r["exit_type"] != "consent_withdrawn":
            g = pt[parts[sid]["part_time"]]
            g[0] += 1
            g[1] += r["exit_type"] == "withdrawal"
    w_all = sum(float(r["base_weight"]) for r in part)
    w_pt = sum(float(r["base_weight"]) for r in part if r["part_time"] == "1")
    share = w_pt / w_all
    p_pt, p_ft = Fraction(pt["1"][1], pt["1"][0]), Fraction(pt["0"][1], pt["0"][0])
    recombined = share * float(p_pt) + (1 - share) * float(p_ft)
    wl, wh = wilson(w0, k0)
    # Chapter 8: p value, power, sample size, and two starting points (points scale)
    d_pts, se_pts = float(diff) * 100, se * 100
    p_two = 2 * normal_cdf(-abs(d_pts) / se_pts)
    z80 = 0.8416212335729143  # the 80th percentile of the standard normal
    # Power and sample size for a true 2-point reduction from the not-offered rate
    delta = Fraction(2, 100)
    q0, q1 = p0, p0 - delta
    se_alt = math.sqrt(float(q0 * (1 - q0) / k0 + q1 * (1 - q1) / k1))
    power2 = normal_cdf(float(delta) / se_alt - Z975) + normal_cdf(-float(delta) / se_alt - Z975)
    n80 = (Z975 + z80) ** 2 * float(q0 * (1 - q0) + q1 * (1 - q1)) / float(delta) ** 2
    m_f, s_f = normal_posterior(d_pts, se_pts)
    m_s, s_s = normal_posterior(d_pts, se_pts, prior_sd=1.0)
    return {
        "invited": str(len(part)),
        "colleges": str(len({r["college_id"] for r in part})),
        "joined": str(len(base)),
        "offered": str(n1),
        "not_offered": str(n0),
        "consent_withdrawn": str(c1 + c0),
        "consent_withdrawn_offered": str(c1),
        "consent_withdrawn_not_offered": str(c0),
        "offered_known": str(k1),
        "not_offered_known": str(k0),
        "withdrew_offered": str(w1),
        "withdrew_not_offered": str(w0),
        "pct_offered_known": pct(p1, 0),
        "pct_not_offered_known": pct(p0, 0),
        "pct_offered_known_1dp": pct(p1),
        "pct_not_offered_known_1dp": pct(p0),
        "pct_offered_all_1dp": pct(Fraction(w1, n1)),
        "pct_not_offered_all_1dp": pct(Fraction(w0, n0)),
        "uptake": str(uptake),
        "transferred_first": str(transferred),
        "uptake_in_10": f"{uptake / n1 * 10:.0f}",
        "difference_points": f"{float(diff) * 100:.1f}",
        "se_points": f"{se * 100:.2f}",
        "ci_low_points": f"{lo * 100:.1f}",
        "ci_high_points": f"{hi * 100:.1f}",
        "did_not_join": str(len(nonresp)),
        "withdrew_did_not_join": str(wn),
        "pct_did_not_join": pct(Fraction(wn, len(nonresp)), 0),
        "pct_did_not_join_1dp": pct(Fraction(wn, len(nonresp))),
        "pct_all_invited_no_offer": pct(all_invited, 0),
        "prob_offer_lowered": f"{lower * 100:.0f}",
        "prob_lowered_2_points": f"{lower_by * 100:.0f}",
        "pt_not_offered_known": str(pt["1"][0]),
        "withdrew_pt": str(pt["1"][1]),
        "pct_pt": pct(p_pt, 0),
        "ft_not_offered_known": str(pt["0"][0]),
        "withdrew_ft": str(pt["0"][1]),
        "pct_ft": pct(p_ft, 0),
        "pct_pt_in_group": pct(Fraction(pt["1"][0], k0), 0),
        "pt_share_weighted_pct": f"{share * 100:.0f}",
        "pct_recombined": f"{recombined * 100:.0f}",
        "wilson_low_pct": f"{wl * 100:.0f}",
        "wilson_high_pct": f"{wh * 100:.0f}",
        "p_two_sided": f"{p_two:.2f}".lstrip("0"),
        "power_pct_2_points": f"{power2 * 100:.0f}",
        "power_one_in": f"{1 / power2:.0f}",
        "n_per_group_80_hundreds": f"{round(n80, -2):,.0f}",
        "times_each_group": f"{n80 / ((n1 + n0) / 2):.0f}",
        "prob_offer_lowered_normal": f"{normal_cdf(-m_f / s_f) * 100:.0f}",
        "prob_offer_lowered_skeptic": f"{normal_cdf(-m_s / s_s) * 100:.0f}",
        "prob_lowered_2_points_skeptic": f"{normal_cdf((-2 - m_s) / s_s) * 100:.0f}",
        **decision(m_f, s_f, m_s, s_s, lo, hi, p0, p1),
        "_normal": {"open": (m_f, s_f), "skeptic": (m_s, s_s)},
        "_pt": {"pt": float(p_pt), "ft": float(p_ft), "mix_study": float(p0), "mix_colleges": recombined},
    }


def decision(m_f, s_f, m_s, s_s, lo, hi, p0, p1):
    """Chapter 18: the mentoring decision with the invented costs above (points scale)."""
    def pays(m, s, value):
        breakeven = COST_PER_STUDENT / value * 100           # points of withdrawal avoided
        return breakeven, normal_cdf((-breakeven - m) / s)   # P(effect lowers withdrawal by more)
    be, pays_open = pays(m_f, s_f, VALUE_AVOIDED)
    _, pays_skeptic = pays(m_s, s_s, VALUE_AVOIDED)
    be_hi, pays_open_hi = pays(m_f, s_f, VALUE_AVOIDED_HIGH)
    _, pays_skeptic_hi = pays(m_s, s_s, VALUE_AVOIDED_HIGH)
    cost_1000 = 1000 * COST_PER_STUDENT
    avoided_open, avoided_skeptic = -m_f * 10, -m_s * 10      # per 1,000 offered
    net_open = avoided_open * VALUE_AVOIDED - cost_1000
    net_skeptic = avoided_skeptic * VALUE_AVOIDED - cost_1000
    n = LARGER_TRIAL_PER_GROUP
    margin = Z975 * math.sqrt(float(p0 * (1 - p0)) / n + float(p1 * (1 - p1)) / n) * 100
    thousands = lambda x: f"{round(x, -3):,.0f}"
    return {
        "breakeven_points": f"{be:.0f}",
        "pays_open_pct": f"{pays_open * 100:.0f}",
        "pays_skeptic_pct": f"{pays_skeptic * 100:.0f}",
        "avoided_open_per_1000": f"{avoided_open:.0f}",
        "value_open_per_1000": thousands(avoided_open * VALUE_AVOIDED),
        "net_open_per_1000": thousands(net_open),
        "avoided_skeptic_per_1000": f"{avoided_skeptic:.0f}",
        "net_skeptic_per_1000": thousands(net_skeptic),
        "trial_per_1000_fewer_more": f"{-lo * 1000:.0f} {hi * 1000:.0f}",
        "breakeven_points_high": f"{be_hi:.0f}",
        "pays_open_high_pct": f"{pays_open_hi * 100:.0f}",
        "pays_skeptic_high_pct": f"{pays_skeptic_hi * 100:.0f}",
        "larger_trial_margin_points": f"{margin:.1f}",
        "larger_trial_interval_at_estimate": f"{-(m_f) - margin:.1f} {-(m_f) + margin:.1f}",
    }


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    companion = Path(sys.argv[1])
    problems = []
    got = analyze(companion, problems)
    for k, want in EXPECTED.items():
        if got.get(k) != want:
            problems.append(f"{k}: the files give {got.get(k)}, the book prints {want}")
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
        print("SPINE_CHECK_FAILED")
        sys.exit(1)
    print(f"SPINE_CHECK_OK values={len(EXPECTED)}{shown}")


if __name__ == "__main__":
    main()
