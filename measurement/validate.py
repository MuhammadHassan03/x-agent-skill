#!/usr/bin/env python3
# Copyright (c) 2026 Muhammad Hassan. MIT License.
"""validate.py - measure postscore.py and the outlier-multiple idea on a public corpus.

This is a research script, NOT part of the plugin. It is the only file in the
repo that needs third-party packages (pyarrow, numpy). The shipped tools do not.

Corpus: huggingface.co/datasets/enryu43/twitter100m_tweets joined to
enryu43/twitter100m_users (follower counts). The dataset declares no licence and X's
Developer Policy forbids redistributing content, so:

  * run it LOCALLY on parquet files you downloaded yourself
  * it prints and writes AGGREGATES ONLY (AUCs, effect sizes, counts)
  * it never writes tweet text, tweet IDs or handles anywhere

Design (all comparisons are WITHIN an account, which removes account size):

  multiple = likes / median likes of that account's original tweets
  hit  = multiple >= 3        miss = multiple < 1

  1. hook AUC       within-account AUC of the hook score, hits vs misses,
                    macro-averaged over accounts, bootstrap CI over accounts
  2. full AUC       same for the full postscore total
  3. baselines      same AUC for trivial features (length, has a number), so the
                    score has to beat something
  4. rule effects   within-account difference in log2(multiple) for tweets that
                    trip a rule vs those that do not (link, bait, hashtag wall,
                    thread opener, question, number in first line)
  5. ranker checks  Spearman of raw likes vs followers, and of the multiple vs
                    followers; and how well a median of k captured posts
                    recovers the true median (why "3 posts" is a floor)

Usage
  python validate.py users.parquet shard1.parquet [shard2.parquet ...] --out results.json
  options: --min-originals 50 --min-median 5 --per-user 200 --seed 7 --since 2019-01-01 --until 2022-12-31

Data era caveat: the corpus ends in April 2023. It predates Premium reach changes,
the open-sourced ranking code, and Original Content Rewards. Treat results as a
test of the heuristics on ordinary tweets, not as a measurement of X today.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

import numpy as np
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "x-post"))
import postscore  # noqa: E402
import xcount  # noqa: E402

NUM = re.compile(r"\d")
Q = re.compile(r"\?")


def auc(pos, neg):
    """Mann-Whitney AUC with tie handling."""
    if len(pos) == 0 or len(neg) == 0:
        return None
    x = np.concatenate([pos, neg])
    ranks = np.empty(len(x))
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    i = 0
    r = np.empty(len(x))
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        r[i:j + 1] = (i + j) / 2 + 1
        i = j + 1
    ranks[order] = r
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def boot_ci(values, n=1000, seed=1):
    v = np.array([x for x in values if x is not None])
    if len(v) == 0:
        return None
    rng = np.random.default_rng(seed)
    means = [rng.choice(v, len(v)).mean() for _ in range(n)]
    return {"mean": round(float(v.mean()), 4), "ci95": [round(float(np.percentile(means, 2.5)), 4),
                                                         round(float(np.percentile(means, 97.5)), 4)], "n_accounts": int(len(v))}


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def load(users_path, shards, since, until, min_orig, min_median, per_user, seed):
    users = pq.read_table(users_path, columns=["user", "followers"]).to_pydict()
    followers = dict(zip(users["user"], users["followers"]))
    rng = random.Random(seed)
    total_rows = matched_rows = 0
    accounts = {}
    for path in shards:
        t = pq.read_table(path, columns=["user", "tweet", "likes", "date"]).to_pydict()
        by = {}
        for u, tw, lk, d in zip(t["user"], t["tweet"], t["likes"], t["date"]):
            total_rows += 1
            if u not in followers:
                continue
            matched_rows += 1
            if not (since <= d[:10] <= until):
                continue
            s = tw.lstrip()
            if s.startswith("@") or s.startswith("RT @") or len(s) < 5:
                continue
            by.setdefault(u, []).append((tw, lk))
        for u, rows in by.items():
            if len(rows) < min_orig:
                continue
            med = float(np.median([lk for _, lk in rows]))
            if med < min_median:
                continue
            rng.shuffle(rows)
            accounts[u] = {"followers": followers[u], "median": med, "rows": rows[:per_user], "all_likes": [lk for _, lk in rows]}
        del t, by
    return accounts, total_rows, matched_rows


def features(text):
    first = postscore.first_line(text)
    bait = bool(postscore.find_bait(text))
    return {
        "hook": postscore.score_hook_line(first)["score"],
        "full": postscore.score(text)["score"],
        "length": float(xcount.count(text)["weighted"]),
        "has_number": float(bool(NUM.search(first))),
        "link": bool(xcount.count(text)["urls"]),
        "bait": bait,
        "hashtag_wall": len(postscore.HASHTAG_RE.findall(text)) > 2,
        "thread_opener": any(p.search(first) for p, _ in postscore.BAD_OPENER_RES[:1]),
        "question": bool(Q.search(text)),
        "number_first": bool(NUM.search(first)),
    }


def main():
    ap = argparse.ArgumentParser(description="Validate postscore and the outlier multiple on a public corpus (aggregates only).")
    ap.add_argument("users")
    ap.add_argument("shards", nargs="+")
    ap.add_argument("--out", default="results.json")
    ap.add_argument("--min-originals", type=int, default=50)
    ap.add_argument("--min-median", type=float, default=5)
    ap.add_argument("--per-user", type=int, default=200)
    ap.add_argument("--max-users", type=int, default=1500)
    ap.add_argument("--since", default="2019-01-01")
    ap.add_argument("--until", default="2022-12-31")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    accounts, total, matched = load(a.users, a.shards, a.since, a.until, a.min_originals, a.min_median, a.per_user, a.seed)
    rng = random.Random(a.seed)
    names = sorted(accounts)
    rng.shuffle(names)
    names = names[:a.max_users]
    res = {"corpus": "twitter100m (ends 2023-04); tweets joined to users on handle", "window": [a.since, a.until],
           "tweet_rows_read": total, "rows_matched_to_users": matched,
           "match_rate": round(matched / max(total, 1), 4), "accounts_used": len(names)}

    hook_auc, full_auc, len_auc, num_auc = [], [], [], []
    effects = {k: [] for k in ("link", "bait", "hashtag_wall", "thread_opener", "question", "number_first")}
    raw_likes, mult_all, fol_all = [], [], []
    n_tweets = n_hits = n_miss = 0
    for u in names:
        acc = accounts[u]
        med = acc["median"]
        feats, mults = [], []
        for tw, lk in acc["rows"]:
            feats.append(features(tw))
            mults.append(lk / med)
        mults = np.array(mults)
        n_tweets += len(mults)
        hit = mults >= 3
        miss = mults < 1
        n_hits += int(hit.sum())
        n_miss += int(miss.sum())
        if hit.sum() >= 3 and miss.sum() >= 3:
            for key, store in (("hook", hook_auc), ("full", full_auc), ("length", len_auc), ("has_number", num_auc)):
                v = np.array([f[key] for f in feats])
                store.append(auc(v[hit], v[miss]))
        lm = np.log2(np.maximum(mults, 1 / 64))
        for key in effects:
            flag = np.array([f[key] for f in feats])
            if flag.sum() >= 5 and (~flag).sum() >= 5:
                effects[key].append(float(lm[flag].mean() - lm[~flag].mean()))
        raw_likes += [lk for _, lk in acc["rows"]]
        mult_all += list(mults)
        fol_all += [acc["followers"]] * len(mults)

    res["tweets_scored"] = n_tweets
    res["hits_ge_3x"] = n_hits
    res["misses_lt_1x"] = n_miss
    res["auc_within_account_hits_vs_misses"] = {
        "hook_score": boot_ci(hook_auc), "full_postscore": boot_ci(full_auc),
        "baseline_length_only": boot_ci(len_auc), "baseline_has_number_in_first_line": boot_ci(num_auc)}
    res["rule_effect_log2_multiple_within_account"] = {
        k: boot_ci(v) for k, v in effects.items()}
    res["rule_effect_note"] = "mean over accounts of mean log2(multiple) with rule minus without; negative = rule goes with fewer likes than that account's norm"
    idx = np.random.default_rng(a.seed).choice(len(raw_likes), min(len(raw_likes), 100000), replace=False)
    rl, ml, fl = np.array(raw_likes)[idx], np.array(mult_all)[idx], np.array(fol_all)[idx]
    res["spearman_with_followers"] = {"raw_likes": round(spearman(rl, fl), 3), "outlier_multiple": round(spearman(ml, fl), 3)}

    # How well do k captured posts recover the true median?
    rng2 = np.random.default_rng(a.seed)
    kerr = {}
    for k in (3, 5, 10, 20):
        errs = []
        for u in names:
            allv = np.array(accounts[u]["all_likes"], dtype=float)
            true = np.median(allv)
            for _ in range(5):
                s = np.median(rng2.choice(allv, k, replace=False))
                errs.append(abs(np.log2(max(s, 0.5) / true)))
        kerr[str(k)] = {"median_abs_log2_error": round(float(np.median(errs)), 3),
                        "p90_abs_log2_error": round(float(np.percentile(errs, 90)), 3)}
    res["baseline_from_k_random_posts"] = kerr
    res["privacy"] = "aggregates only; no tweet text, IDs or handles are written"
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
