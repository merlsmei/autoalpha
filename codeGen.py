"""
codeGen.py — Alpha Java Code Generator

Reads codeGenPolicy.md and automatically finds the alpha equation with the
smallest number that has not yet been implemented. Calls the DeepSeek API
to produce a compilable Java implementation, saved to java/alphaCodeN.java.

Equation files:  equations/alphaN.md
Java output:     java/alphaCodeN.java

Usage:
    python codeGen.py
    python codeGen.py --policy codeGenPolicy.md

Requirements:
    pip install openai

Environment:
    DEEPSEEK_API_KEY — your DeepSeek API key (required)
"""

import argparse
import os
import re
import sys
from pathlib import Path


def load_file(path: Path, label: str) -> str:
    if not path.exists():
        print(f"Error: {label} not found at {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def find_next_unimplemented(equations_dir: Path, java_dir: Path) -> int | None:
    """Return the smallest alpha number present in equations/ but missing in java/."""
    if not equations_dir.exists():
        return None
    eq_nums = {
        int(m.group(1))
        for f in equations_dir.iterdir()
        if (m := re.fullmatch(r"alpha(\d+)\.md", f.name))
    }
    if not eq_nums:
        return None
    impl_nums = set()
    if java_dir.exists():
        impl_nums = {
            int(m.group(1))
            for f in java_dir.iterdir()
            if (m := re.fullmatch(r"alphaCode(\d+)\.java", f.name))
        }
    pending = sorted(eq_nums - impl_nums)
    return pending[0] if pending else None


def build_messages(policy_text: str, eq_text: str, eq_num: int) -> list[dict]:
    system_prompt = (
        "You are an expert Java engineer implementing quantitative alpha strategies for a systematic trading system. "
        "You will be given a code generation policy and an alpha equation specification. "
        "Your output must be a complete, compilable Java source file that strictly follows the policy. "
        "Output only the raw Java source code — no markdown, no explanation, no code fences."
    )

    user_prompt = (
        "Below is the Java Code Generation Policy. Follow it exactly.\n\n"
        f"---\n{policy_text}\n---\n\n"
        f"Below is the alpha equation to implement (Alpha {eq_num}):\n\n"
        f"---\n{eq_text}\n---\n\n"
        f"Implement this alpha as `AlphaCode{eq_num}` following all rules in the policy. "
        f"The class must be in file `alphaCode{eq_num}.java`, package `alpha`, and implement `AlphaStrategy`. "
        "Output only the raw Java source code."
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
        temperature=0.2,
    )
    return response.choices[0].message.content


def strip_code_fences(text: str) -> str:
    """Remove markdown ```java ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    match = re.match(r"^```(?:java)?\n(.*?)```$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Java alpha implementation using DeepSeek and codeGenPolicy.md. "
            "Automatically picks the smallest equation number not yet implemented."
        )
    )
    parser.add_argument(
        "--policy",
        type=str,
        default=None,
        help="Path to the code generation policy file (default: codeGenPolicy.md next to this script)",
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
    policy_path = Path(args.policy) if args.policy else script_dir / "codeGenPolicy.md"
    equations_dir = script_dir / "equations"
    java_dir = script_dir / "java"

    eq_num = find_next_unimplemented(equations_dir, java_dir)
    if eq_num is None:
        print("All equations are already implemented.")
        sys.exit(0)

    eq_path = equations_dir / f"alpha{eq_num}.md"
    out_path = java_dir / f"alphaCode{eq_num}.java"

    policy_text = load_file(policy_path, "code generation policy")
    eq_text = load_file(eq_path, f"alpha equation {eq_num}")

    messages = build_messages(policy_text, eq_text, eq_num)

    print(f"Generating Java implementation for Alpha {eq_num} ({eq_path.name} → {out_path.name})...\n")

    raw = call_deepseek(messages, api_key)
    java_code = strip_code_fences(raw)

    java_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(java_code, encoding="utf-8")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
