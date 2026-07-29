#!/usr/bin/env python3
"""quant.py — stdlib statistics/linear algebra for invest-optimizer tools.
No numpy; everything is small (n <= ~15 assets, T <= ~130 days)."""
import math, random


# --- series ------------------------------------------------------------------
def log_returns(closes):
    return [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def stdev(xs):
    return math.sqrt(variance(xs))


def percentile(xs, p):
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    return s[int(k)] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def max_drawdown(xs):
    """xs = cumulative simple-return equity curve starting at 1."""
    peak, mdd = 1.0, 0.0
    for x in xs:
        peak = max(peak, x)
        mdd = min(mdd, x / peak - 1.0)
    return mdd


# --- matrices ------------------------------------------------------------------
def cov_matrix(series):
    """series = list of return-lists (aligned, equal length) -> covariance matrix."""
    n = len(series)
    ms = [mean(s) for s in series]
    T = len(series[0])
    return [[sum((series[i][t] - ms[i]) * (series[j][t] - ms[j]) for t in range(T)) / (T - 1)
             for j in range(n)] for i in range(n)]


def corr_matrix(cov):
    n = len(cov)
    sd = [math.sqrt(max(cov[i][i], 1e-18)) for i in range(n)]
    return [[cov[i][j] / (sd[i] * sd[j]) for j in range(n)] for i in range(n)]


def solve(A, b):
    """Gaussian elimination with partial pivot. A is n x n, b length n."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-14:
            raise ValueError("singular matrix")
        M[col], M[piv] = M[piv], M[col]
        for r in range(col + 1, n):
            f = M[r][col] / M[col][col]
            M[r] = [x - f * y for x, y in zip(M[r], M[col])]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))) / M[r][r]
    return x


def portfolio_var(w, cov):
    return sum(w[i] * cov[i][j] * w[j] for i in range(len(w)) for j in range(len(w)))


def effective_n(w):
    return 1.0 / sum(x * x for x in w) if any(w) else 0.0


# --- HRP (Lopez de Prado) -------------------------------------------------------
def _dist(corr):
    n = len(corr)
    return [[math.sqrt(max(0.0, (1 - corr[i][j]) / 2)) for j in range(n)] for i in range(n)]


def _linkage(dist):
    """Average-linkage agglomerative clustering -> merge list [(a,b,d,members)]."""
    clusters = {i: [i] for i in range(len(dist))}
    next_id = len(dist)
    merges = []
    while len(clusters) > 1:
        ids = sorted(clusters)
        best = None
        for x in range(len(ids)):
            for y in range(x + 1, len(ids)):
                a, b = ids[x], ids[y]
                d = mean([dist[i][j] for i in clusters[a] for j in clusters[b]])
                if best is None or d < best[2]:
                    best = (a, b, d)
        a, b, d = best
        clusters[next_id] = clusters.pop(a) + clusters.pop(b)
        merges.append((a, b, d, clusters[next_id]))
        next_id += 1
    return merges


def _hrp_order(merges, n):
    """Leaf order of the merge tree (quasi-diagonalization). Root id = 2n-2."""
    def items(node):
        if node < n:
            return [node]
        a, b = merges[node - n][0], merges[node - n][1]
        return items(a) + items(b)
    return items(2 * n - 2)


def hrp(cov):
    """Hierarchical Risk Parity weights from a covariance matrix."""
    n = len(cov)
    if n == 1:
        return [1.0]
    corr = corr_matrix(cov)
    dist = _dist(corr)
    merges = _linkage(dist)
    order = _hrp_order(merges, n)
    ivp = [1.0 / max(cov[i][i], 1e-18) for i in range(n)]
    w = [1.0] * n

    def cluster_var(items):
        sub = [[cov[i][j] for j in items] for i in items]
        iw = [ivp[i] for i in items]
        s = sum(iw)
        iw = [x / s for x in iw]
        return portfolio_var(iw, sub)

    clusters = [order]
    while clusters:
        nxt = []
        for c in clusters:
            if len(c) <= 1:
                continue
            half = len(c) // 2
            c1, c2 = c[:half], c[half:]
            v1, v2 = cluster_var(c1), cluster_var(c2)
            alpha = 1 - v1 / (v1 + v2) if (v1 + v2) > 0 else 0.5
            for i in c1:
                w[i] *= alpha
            for i in c2:
                w[i] *= (1 - alpha)
            nxt += [c1, c2]
        clusters = nxt
    s = sum(w)
    return [x / s for x in w]


# --- misc optimizers -------------------------------------------------------------
def inverse_vol(cov):
    iv = [1.0 / math.sqrt(max(cov[i][i], 1e-18)) for i in range(len(cov))]
    s = sum(iv)
    return [x / s for x in iv]


def min_variance(cov):
    """Long-only min-variance: KKT solve, iterate clipping negatives."""
    n = len(cov)
    active = list(range(n))
    for _ in range(n + 1):
        k = len(active)
        A = [[cov[active[i]][active[j]] for j in range(k)] + [1.0] for i in range(k)]
        A.append([1.0] * k + [0.0])
        b = [0.0] * k + [1.0]
        sol = solve(A, b)[:k]
        w = {active[i]: sol[i] for i in range(k)}
        negs = [i for i in active if w[i] < 0]
        if not negs:
            out = [w.get(i, 0.0) for i in range(n)]
            s = sum(out)
            return [x / s for x in out]
        for i in negs:
            active.remove(i)
    return inverse_vol(cov)


def risk_parity(cov, iters=500):
    """Equal risk contribution via cyclical coordinate descent."""
    n = len(cov)
    w = [1.0 / n] * n
    for _ in range(iters):
        pv = math.sqrt(max(portfolio_var(w, cov), 1e-18))
        for i in range(n):
            mrc = sum(cov[i][j] * w[j] for j in range(n)) / pv
            trc = pv / n  # target risk contribution: w_i * mrc_i = pv / n
            if mrc > 1e-12:
                w[i] = max(w[i] * math.sqrt(trc / max(w[i] * mrc, 1e-18)), 1e-8)
        s = sum(w)
        w = [x / s for x in w]
    return w


def shock_corr(cov, bump=0.3):
    """Uniform +bump correlation shock (correlation-break stress check)."""
    corr = corr_matrix(cov)
    n = len(cov)
    sd = [math.sqrt(cov[i][i]) for i in range(n)]
    return [[(min(1.0, corr[i][j] + bump) if i != j else 1.0) * sd[i] * sd[j]
             for j in range(n)] for i in range(n)]


# --- Monte Carlo ------------------------------------------------------------------
def mc_bust(returns, loss_tol, horizon=63, paths=1000, seed=42):
    """Bootstrap resample daily log returns; bust = maxDD <= -loss_tol within horizon."""
    rng = random.Random(seed)
    busts = 0
    for _ in range(paths):
        eq, peak, mdd = 1.0, 1.0, 0.0
        for _ in range(horizon):
            eq *= math.exp(rng.choice(returns))
            peak = max(peak, eq)
            mdd = min(mdd, eq / peak - 1.0)
        if mdd <= -loss_tol:
            busts += 1
    return busts / paths
