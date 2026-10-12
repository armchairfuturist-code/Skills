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


if __name__ == "__main__":
    unittest.main(verbosity=2)