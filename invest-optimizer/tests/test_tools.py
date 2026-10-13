#!/usr/bin/env python3
"""Regression tests for the invest-optimizer tools (stdlib only).

Run:  python3 tests/test_tools.py
"""
import contextlib
import io
import json
import math
import pathlib
import sys
import unittest
from unittest import mock

TOOLS = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import evaluate
import optimize
import quant
import risk


def history_for(ticker, n=70):
    """Distinct synthetic closes per ticker, shaped like feeds.closes output."""
    seed = sum(ord(c) for c in ticker)
    dates = [f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]
    closes = [100.0 * math.exp(0.0005 * i + 0.012 * math.sin(i / 3 + seed)) for i in range(n)]
    return list(zip(dates, closes))


def falling_history(ticker, n=70):
    """Mostly falling closes, so the worst 5% of days are clearly negative."""
    seed = sum(ord(c) for c in ticker)
    dates = [f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]
    closes = [100.0 * math.exp(-0.004 * i + 0.010 * math.sin(i / 3 + seed)) for i in range(n)]
    return list(zip(dates, closes))


def run_cli(module, argv, history=history_for, mc_bust=None):
    """Drive a tool's real main() and return its captured stdout."""
    out = io.StringIO()
    patches = [mock.patch.object(sys, "argv", [module.__name__] + argv),
               mock.patch.object(module.feeds, "closes", side_effect=history)]
    if mc_bust is not None:
        patches.append(mock.patch.object(module, "mc_bust", return_value=mc_bust))
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        stack.enter_context(contextlib.redirect_stdout(out))
        exit_code = None
        try:
            module.main()
        except SystemExit as e:
            exit_code = e.code
    return out.getvalue(), exit_code


class CapWeightsTest(unittest.TestCase):
    def test_infeasible_cap_is_rejected(self):
        # 2 names cannot honour a 30% cap. Clipping used to return [0.5, 0.5].
        with self.assertRaises(optimize.InfeasibleError):
            optimize.cap_weights([0.8, 0.2], 0.30)

    def test_feasible_cap_is_honoured_after_renormalization(self):
        w = optimize.cap_weights([0.8, 0.15, 0.05], 0.50)
        self.assertLessEqual(max(w), 0.50)
        self.assertAlmostEqual(sum(w), 1.0, places=9)

    def test_every_model_respects_a_feasible_cap(self):
        series = [[0.01, -0.02, 0.03, 0.01, 0.00],
                  [0.02, 0.01, -0.01, 0.02, 0.01],
                  [-0.01, 0.02, 0.01, -0.02, 0.00],
                  [0.03, -0.01, 0.02, 0.01, -0.01]]
        cov = quant.cov_matrix(series)
        for name, model in optimize.MODELS.items():
            with self.subTest(model=name):
                w = optimize.cap_weights(model(cov), 0.40)
                self.assertLessEqual(max(w), 0.40 + 1e-9)
                self.assertAlmostEqual(sum(w), 1.0, places=9)


class PortfolioReturnTest(unittest.TestCase):
    def test_equal_weight_half_up_and_half_down_is_flat(self):
        # +50% and -50% at equal weight nets to 0%, not -13.4% from summing logs.
        simple = quant.portfolio_simple_returns([0.5, 0.5],
                                                [[math.log(1.5)], [math.log(0.5)]])
        self.assertAlmostEqual(simple[0], 0.0, places=12)

    def test_log_series_is_log1p_of_the_simple_series(self):
        asset = [[0.10, -0.05, 0.02], [0.02, 0.03, -0.01]]
        logs = quant.portfolio_log_returns([0.6, 0.4], asset)
        simple = quant.portfolio_simple_returns([0.6, 0.4], asset)
        self.assertEqual(len(logs), 3)
        for lg, sp in zip(logs, simple):
            self.assertAlmostEqual(lg, math.log1p(sp), places=12)

    def test_asset_input_is_log_space(self):
        # A flat 0.05 input is a log return, so the mix returns expm1(0.05).
        asset = [[0.05, 0.05], [0.05, 0.05]]
        simple = quant.portfolio_simple_returns([0.5, 0.5], asset)
        self.assertAlmostEqual(simple[0], math.expm1(0.05), places=12)


class CorrelationShockTest(unittest.TestCase):
    COV = [[1.0, -0.9, -0.1],
           [-0.9, 1.0, 0.5],
           [-0.1, 0.5, 1.0]]

    def test_input_is_positive_semi_definite(self):
        self.assertTrue(quant.is_psd(self.COV))

    def test_shock_stays_positive_semi_definite(self):
        # The old additive +0.3 bump made this matrix indefinite (det -0.232).
        self.assertTrue(quant.is_psd(quant.shock_corr(self.COV)))

    def test_shock_keeps_unit_diagonal_and_raises_off_diagonals(self):
        corr = quant.corr_matrix(quant.shock_corr(self.COV))
        self.assertAlmostEqual(corr[0][0], 1.0, places=12)
        self.assertAlmostEqual(corr[0][1], 0.7 * -0.9 + 0.3, places=9)
        self.assertAlmostEqual(corr[1][2], 0.7 * 0.5 + 0.3, places=9)

    def test_psd_check_flags_an_indefinite_matrix(self):
        indefinite = [[1.0, 0.9, 0.9],
                      [0.9, 1.0, -0.9],
                      [0.9, -0.9, 1.0]]
        self.assertFalse(quant.is_psd(indefinite))


class RiskGateTest(unittest.TestCase):
    POSITIONS = ["AAA:0.5", "BBB:0.5", "--json"]

    def test_conservative_gate_fails_a_bust_that_moderate_passes(self):
        moderate, _ = run_cli(risk, self.POSITIONS, mc_bust=0.15)
        conservative, _ = run_cli(risk, self.POSITIONS + ["--gate", "0.10"], mc_bust=0.15)
        self.assertEqual(json.loads(moderate)["mc"]["gate"], "PASS")
        self.assertEqual(json.loads(moderate)["mc"]["gate_p"], 0.25)
        self.assertTrue(json.loads(conservative)["mc"]["gate"].startswith("FAIL"))
        self.assertEqual(json.loads(conservative)["mc"]["gate_p"], 0.10)

    def test_gate_limit_is_echoed_in_json(self):
        payload, _ = run_cli(risk, self.POSITIONS + ["--gate", "0.05"], mc_bust=0.15)
        self.assertEqual(json.loads(payload)["mc"]["gate_p"], 0.05)

    def test_cvar95_is_the_mean_of_days_worse_than_var95(self):
        out, _ = run_cli(risk, self.POSITIONS, mc_bust=0.0)
        payload = json.loads(out)
        self.assertLessEqual(payload["daily_cvar95"], payload["daily_var95"])

    def test_mix_return_is_the_weighted_average_of_simple_returns(self):
        # AAA halves while BBB is flat. A 50/50 mix loses 25%, not the ~29.3%
        # that a weighted sum of log returns implies.
        side = {"AAA": [("2026-01-01", 100.0), ("2026-01-02", 50.0), ("2026-01-03", 50.0)],
                "BBB": [("2026-01-01", 100.0), ("2026-01-02", 100.0), ("2026-01-03", 100.0)]}
        out, _ = run_cli(risk, ["AAA:0.5", "BBB:0.5", "--json"],
                         history=lambda t: side[t], mc_bust=0.0)
        payload = json.loads(out)
        self.assertEqual(payload["max_drawdown"], -0.25)
        self.assertEqual(payload["obs"], 2)


class CovarianceTest(unittest.TestCase):
    SERIES = [[math.sin(t * 1.7 + k) * 0.01 + 0.001 * k + 0.0004 * t for t in range(16)]
              for k in range(3)]

    # sklearn.covariance.LedoitWolf on SERIES, shrinkage 0.2296705288990897.
    # Pins the closed form to the reference implementation.
    GOLDEN = [[4.933723563983556e-05, 2.1635390610225008e-05, -1.2330951538838385e-05],
              [2.1635390610225008e-05, 5.368477770983383e-05, 2.5400154253676605e-05],
              [-1.2330951538838385e-05, 2.5400154253676605e-05, 5.477033556092045e-05]]

    def test_matches_the_sklearn_reference(self):
        got = quant.ledoit_wolf(self.SERIES)
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(got[i][j], self.GOLDEN[i][j], places=12)

    def test_single_asset_returns_its_sample_variance(self):
        # d2 is zero for one asset, so shrinkage is total and the result is mu.
        series = [[0.01, -0.02, 0.03, 0.01]]
        m = sum(series[0]) / 4
        variance = sum((v - m) ** 2 for v in series[0]) / 4
        self.assertAlmostEqual(quant.ledoit_wolf(series)[0][0], variance, places=12)

    def test_shrunk_matrix_is_positive_semi_definite(self):
        self.assertTrue(quant.is_psd(quant.ledoit_wolf(self.SERIES)))

    def test_needs_at_least_two_observations(self):
        with self.assertRaises(ValueError):
            quant.ledoit_wolf([[0.01], [0.02]])


class OptimizeCliTest(unittest.TestCase):
    def test_feasible_cap_holds_end_to_end(self):
        out, code = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.40", "--json"])
        self.assertIsNone(code)
        payload = json.loads(out)
        self.assertLessEqual(max(payload["weights"].values()), 0.40 + 1e-9)
        self.assertAlmostEqual(sum(payload["weights"].values()), 1.0, places=9)
        self.assertEqual(payload["cap"], 0.40)

    def test_infeasible_cap_emits_no_weights_and_exits_two(self):
        out, code = run_cli(optimize, ["AAA", "BBB", "--cap", "0.30"])
        self.assertEqual(code, 2)
        self.assertIn("NO ALLOCATION EMITTED", out)
        self.assertNotIn("sum 100.00%", out)

    def test_reported_cvar95_is_negative_on_a_falling_market(self):
        out, _ = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.5", "--json"],
                         history=falling_history)
        payload = json.loads(out)
        self.assertLess(payload["daily_cvar95"], 0.0)
        self.assertGreater(payload["daily_cvar95"], -1.0)

    def test_default_covariance_is_ledoit_wolf(self):
        out, _ = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.5", "--json"])
        self.assertEqual(json.loads(out)["cov"], "lw")

    def test_cov_flag_selects_the_estimator(self):
        out, _ = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.5",
                                    "--cov", "sample", "--json"])
        payload = json.loads(out)
        self.assertEqual(payload["cov"], "sample")
        self.assertEqual(sorted(payload["weights"]), ["AAA", "BBB", "CCC"])

    def test_cov_value_is_not_parsed_as_a_ticker(self):
        out, _ = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.5",
                                    "--cov", "lw", "--json"])
        self.assertNotIn("LW", json.loads(out)["weights"])

    def test_unknown_covariance_exits_one(self):
        _, code = run_cli(optimize, ["AAA", "BBB", "CCC", "--cap", "0.5",
                                     "--cov", "bogus"])
        self.assertEqual(code, 1)


class RollForwardTest(unittest.TestCase):
    def test_flat_market_holds_value_with_no_rebalancing_cost(self):
        rets = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        curve, traded, _ = evaluate.roll(rets, evaluate.equal_weight_policy(2), 1, 25.0)
        self.assertEqual(curve, [1.0, 1.0, 1.0, 1.0])
        self.assertEqual(traded, 0.0)

    def test_hold_after_one_rebalance_equals_buy_and_hold(self):
        # A +10% then +20%, B flat, equal weight, no further rebalance:
        # 0.5 * 1.10 * 1.20 + 0.5 * 1.00 = 1.16
        rets = [[0.10, 0.20], [0.00, 0.00]]
        curve, traded, held = evaluate.roll(rets, evaluate.equal_weight_policy(2),
                                            len(rets[0]), 0.0)
        self.assertAlmostEqual(curve[-1], 1.16, places=12)
        self.assertEqual(traded, 0.0)
        self.assertEqual(held, 0)

    def test_costs_reduce_wealth_when_the_policy_trades(self):
        rets = [[0.01, -0.01], [-0.01, 0.01]]
        flip = lambda history: [1.0, 0.0] if len(history[0]) % 2 == 0 else [0.0, 1.0]
        free, _, _ = evaluate.roll(rets, flip, 1, 0.0)
        costly, _, _ = evaluate.roll(rets, flip, 1, 100.0)
        self.assertLess(costly[-1], free[-1])

    def test_a_policy_receives_only_returns_before_the_rebalance(self):
        seen = []

        def spy(history):
            seen.append(len(history[0]))
            return [0.5, 0.5]

        evaluate.roll([[0.01] * 6, [0.02] * 6], spy, 2, 0.0)
        self.assertEqual(seen, [0, 2, 4])

    def test_unfit_rebalances_are_held_and_counted(self):
        def never_fits(history):
            raise optimize.InfeasibleError("no fit")

        rets = [[0.01] * 6, [0.02] * 6]
        curve, traded, held = evaluate.roll(rets, never_fits, 2, 10.0)
        self.assertEqual(held, 3)
        self.assertEqual(traded, 0.0)
        # Held weights drift, which is buy and hold of the initial 50/50:
        # 0.5 * 1.01**6 + 0.5 * 1.02**6
        self.assertAlmostEqual(curve[-1], 0.5 * 1.01 ** 6 + 0.5 * 1.02 ** 6, places=12)

    def test_summarize_reports_compounded_growth(self):
        summary = evaluate.summarize([1.0, 1.1, 1.21], 0.0, 0)
        self.assertEqual(summary["days"], 2)
        self.assertAlmostEqual(summary["growth"], 1.21, places=9)
        self.assertEqual(summary["max_drawdown"], 0.0)

    def test_fixed_policy_fits_with_shrinkage_and_the_cap(self):
        history = [[0.01, -0.02, 0.03, 0.01, 0.005],
                   [0.005, 0.01, -0.01, 0.02, 0.001],
                   [-0.01, 0.02, 0.01, -0.02, 0.004]]
        got = evaluate.fixed_policy(quant.hrp, 0.5, window=5)(history)
        expected = optimize.cap_weights(quant.hrp(quant.ledoit_wolf(history)), 0.5)
        self.assertEqual(got, expected)

    def test_insufficient_history_exits_two_with_the_requirement(self):
        out, code = run_cli(evaluate, ["AAA", "BBB", "--window", "500", "--step", "21"])
        self.assertEqual(code, 2)
        self.assertIn("needs 522", out)

    def test_warmup_keeps_the_reported_path_policy_live(self):
        seen = []

        def spy(history):
            seen.append(len(history[0]))
            return [0.5, 0.5]

        curve, _, held = evaluate.roll([[0.01] * 6, [0.02] * 6], spy, 2, 0.0, warmup=2)
        self.assertEqual(seen, [2, 4])
        self.assertEqual(held, 0)
        self.assertEqual(len(curve) - 1, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)