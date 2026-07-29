#!/usr/bin/env python3
"""hmm.py — 2-state Gaussian HMM on daily log returns (stdlib only).
Confirmation layer for Phase 2G: current regime, persistence, stationary mix.
125 observations is thin — treat output as a tension flag, never an override."""
import math

from quant import mean, variance


def _gauss(x, mu, var):
    var = max(var, 1e-10)
    return math.exp(-((x - mu) ** 2) / (2 * var)) / math.sqrt(2 * math.pi * var)


def fit_hmm(returns, iters=100):
    """Baum-Welch EM with log-space forward-backward. Returns state params,
    transition matrix, filtered prob of state-1 (last obs), stationary mix.
    State labels are normalized: 0 = lower-vol, 1 = higher-vol."""
    n = 2
    T = len(returns)
    mu = [mean(returns) - 0.005, mean(returns) + 0.005]
    var = [variance(returns)] * 2
    A = [[0.9, 0.1], [0.1, 0.9]]
    pi = [0.5, 0.5]

    for _ in range(iters):
        B = [[max(_gauss(returns[t], mu[s], var[s]), 1e-300) for t in range(T)] for s in range(n)]
        # forward (log-space)
        la = [[0.0] * T for _ in range(n)]
        for s in range(n):
            la[s][0] = math.log(max(pi[s] * B[s][0], 1e-300))
        for t in range(1, T):
            for s in range(n):
                vals = [la[p][t - 1] + math.log(max(A[p][s], 1e-300)) for p in range(n)]
                m = max(vals)
                la[s][t] = math.log(B[s][t]) + m + math.log(sum(math.exp(v - m) for v in vals))
        # backward
        lb = [[0.0] * T for _ in range(n)]
        for t in range(T - 2, -1, -1):
            for s in range(n):
                vals = [math.log(max(A[s][p], 1e-300)) + math.log(B[p][t + 1]) + lb[p][t + 1]
                        for p in range(n)]
                m = max(vals)
                lb[s][t] = m + math.log(sum(math.exp(v - m) for v in vals))
        # gamma / xi
        gamma = [[0.0] * T for _ in range(n)]
        for t in range(T):
            vals = [la[s][t] + lb[s][t] for s in range(n)]
            m = max(vals)
            exps = [math.exp(v - m) for v in vals]
            tot = sum(exps)
            for s in range(n):
                gamma[s][t] = exps[s] / tot
        xi_sum = [[0.0] * n for _ in range(n)]
        for t in range(T - 1):
            vals = [[la[i][t] + math.log(max(A[i][j], 1e-300)) + math.log(B[j][t + 1]) + lb[j][t + 1]
                     for j in range(n)] for i in range(n)]
            m = max(max(r) for r in vals)
            exps = [[math.exp(v - m) for v in r] for r in vals]
            tot = sum(sum(r) for r in exps)
            for i in range(n):
                for j in range(n):
                    xi_sum[i][j] += exps[i][j] / tot
        # M-step
        for s in range(n):
            gs = sum(gamma[s])
            mu[s] = sum(gamma[s][t] * returns[t] for t in range(T)) / gs
            var[s] = max(sum(gamma[s][t] * (returns[t] - mu[s]) ** 2 for t in range(T)) / gs, 1e-10)
            for j in range(n):
                A[s][j] = xi_sum[s][j] / gs
        pi = [gamma[s][0] for s in range(n)]

    # normalize labels: state 1 = higher variance ("Bear/turbulent")
    if var[0] > var[1]:
        mu, var = [mu[1], mu[0]], [var[1], var[0]]
        A = [[A[1][1], A[1][0]], [A[0][1], A[0][0]]]
        pi = [pi[1], pi[0]]
        gamma = [gamma[1], gamma[0]]

    # stationary distribution from A
    p01, p10 = A[0][1], A[1][0]
    stat0 = p10 / (p01 + p10) if (p01 + p10) > 0 else 0.5
    return {
        "mu_ann": [mu[s] * 252 for s in range(2)],
        "vol_ann": [math.sqrt(var[s] * 252) for s in range(2)],
        "p_stay": [A[0][0], A[1][1]],
        "stationary": [stat0, 1 - stat0],
        "p_turbulent_now": gamma[1][-1],
        "obs": T,
    }


def regime_report(returns):
    r = fit_hmm(returns)
    bull = r["p_turbulent_now"] < 0.35
    bear = r["p_turbulent_now"] > 0.65
    r["regime"] = "BEAR/TURBULENT" if bear else ("BULL/CALM" if bull else "MIXED")
    return r
