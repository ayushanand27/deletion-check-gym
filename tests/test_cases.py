from collections import Counter

from gym.cases import PLAN, generate_cases


def test_case_count_and_unique_ids():
    cases = generate_cases()
    assert len(cases) == sum(n for _, n in PLAN) == 40
    assert len({c["case_id"] for c in cases}) == 40


def test_same_seed_same_cases():
    assert generate_cases(7) == generate_cases(7)
    assert generate_cases(7) != generate_cases(8)


def test_category_counts():
    counts = Counter(c["category"] for c in generate_cases())
    assert dict(counts) == dict(PLAN)


def test_cases_do_not_store_the_answer():
    for c in generate_cases():
        assert set(c) == {"case_id", "category", "records"}


def test_missing_record_cases_really_miss_a_system():
    from gym.constants import ALL_SYSTEMS
    for c in generate_cases():
        if c["category"] == "missing_record":
            assert len({r["system"] for r in c["records"]}) < len(ALL_SYSTEMS)
