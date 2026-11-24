from agents.baselines import ReferenceAgent
from agents.interactive_agents import ThoroughAgent
from gym import generate_cases
from harness.evaluate import (bootstrap_ci, category_table, evaluate_interactive,
                              evaluate_single, markdown_table)

CASES = generate_cases()


def test_bootstrap_ci_brackets_the_mean():
    mean, lo, hi = bootstrap_ci([1.0, 0.0, 1.0, 0.0, 1.0])
    assert lo <= mean <= hi


def test_bootstrap_ci_constant_values():
    assert bootstrap_ci([0.5] * 10) == (0.5, 0.5, 0.5)


def test_evaluate_single_reference_is_perfect():
    s = evaluate_single(ReferenceAgent(), CASES)
    assert "1.00" in markdown_table([s])


def test_evaluate_interactive_thorough_is_correct():
    s = evaluate_interactive(ThoroughAgent(), CASES)
    table = markdown_table([s], interactive=True)
    assert "Mean steps" in table and "40/40" in table


def test_category_table_lists_every_category():
    s = evaluate_single(ReferenceAgent(), CASES)
    t = category_table([s])
    for cat in {c["category"] for c in CASES}:
        assert cat in t
