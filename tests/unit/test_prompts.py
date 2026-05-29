import pytest

from src.llm.prompts import load_prompt

PROMPTS = [
    "router",
    "cooking/inventory",
    "cooking/recipe",
    "cooking/substitution",
    "home/classifier",
    "home/diagnosis",
    "home/diy",
    "home/pro",
    "home/prevention",
]


@pytest.mark.parametrize("name", PROMPTS)
def test_prompt_loads_and_nonempty(name: str) -> None:
    text = load_prompt(name)
    assert text.strip()


def test_missing_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does/not/exist")
