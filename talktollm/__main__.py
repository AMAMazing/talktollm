import argparse
from . import talkto

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with language models.")
    parser.add_argument("llm", help="The language model to use (e.g., 'gemini', 'deepseek').")
    parser.add_argument("prompt", help="The prompt for the language model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for verbose output.")
    parser.add_argument("--fast-mode", action="store_true", help="Enable fast mode with interface check and background tab reset.")
    args = parser.parse_args()

    talkto(args.llm, args.prompt, debug=args.debug, fast_mode=args.fast_mode)