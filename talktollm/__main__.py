import argparse
from . import talkto

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with language models.")
    parser.add_argument("llm", help="The language model to use (e.g., 'gemini', 'deepseek').")
    parser.add_argument("prompt", help="The prompt for the language model.")
    args = parser.parse_args()

    talkto(args.llm, args.prompt)
