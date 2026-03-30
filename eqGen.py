"""
eqGen.py — Alpha Equation Generator

Reads eqGenPolicy.md and uses the DeepSeek API to generate a novel alpha
equation that conforms to the policy rules.

Usage:
    python eqGen.py
    python eqGen.py --theme momentum
    python eqGen.py --theme mean-reversion --n 3

Requirements:
    pip install openai

Environment:
    DEEPSEEK_API_KEY — your DeepSeek API key (required)
"""

import argparse
import os
import sys
from pathlib import Path


def load_policy(policy_path: Path) -> str:
    if not policy_path.exists():
        print(f"Error: policy file not found at {policy_path}", file=sys.stderr)
        sys.exit(1)
    return policy_path.read_text(encoding="utf-8")


def build_messages(policy_text: str, theme: str | None, n: int) -> list[dict]:
    system_prompt = (
        "You are an expert quantitative researcher specializing in systematic equity strategies. "
        "Your task is to generate novel alpha expressions (trading signals) for a stock universe. "
        "You must strictly follow the policy rules provided by the user — no exceptions. "
        "Every alpha you produce must use only the operators and data fields defined in the policy. "
        "Output each alpha in exactly the format specified in the policy's Output Format section."
    )

    theme_clause = ""
    if theme:
        theme_clause = f"\n\nFocus on the **{theme}** signal type. All generated alphas should reflect this theme."

    count_clause = f"Generate exactly {n} alpha equation{'s' if n > 1 else ''}."
    if n > 1:
        count_clause += " Each alpha must represent a distinct signal — do not produce near-duplicates."

    user_prompt = (
        f"Below is the Alpha Equation Generation Policy. Read it carefully before generating any alpha.\n\n"
        f"---\n{policy_text}\n---\n\n"
        f"{count_clause}{theme_clause}\n\n"
        "For each alpha, produce the four required fields from the Output Format section:\n"
        "1. Equation\n"
        "2. Rationale\n"
        "3. Signal type\n"
        "4. Lookback horizon\n\n"
        "Do not output anything outside these fields. Do not repeat or paraphrase the policy."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_deepseek(messages: list[dict], api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        print(
            "Error: 'openai' package is not installed. Run: pip install openai",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=1.0,
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(
        description="Generate alpha equations using DeepSeek and eqGenPolicy.md"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default=None,
        help="Signal theme to focus on (e.g. momentum, mean-reversion, liquidity, volatility, value)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of alpha equations to generate (default: 1)",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=None,
        help="Path to the policy markdown file (default: eqGenPolicy.md next to this script)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print(
            "Error: DEEPSEEK_API_KEY environment variable is not set.\n"
            "Export it before running: export DEEPSEEK_API_KEY=<your-key>",
            file=sys.stderr,
        )
        sys.exit(1)

    script_dir = Path(__file__).parent
    policy_path = Path(args.policy) if args.policy else script_dir / "eqGenPolicy.md"

    policy_text = load_policy(policy_path)
    messages = build_messages(policy_text, theme=args.theme, n=args.n)

    print(f"Generating {args.n} alpha equation(s)" + (f" [theme: {args.theme}]" if args.theme else "") + "...\n")

    result = call_deepseek(messages, api_key)
    print(result)


if __name__ == "__main__":
    main()
