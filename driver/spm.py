import argparse
from pathlib import Path

import sentencepiece as spm


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("spm_model_path")
    args = parser.parse_args()

    spm_model_path = Path(args.spm_model_path)
    assert spm_model_path.is_file()

    processor = spm.SentencePieceProcessor(str(spm_model_path))
    print(f"length of processor: {len(processor)}")

    # TODO This makes too long output. Let's make tabular.
    def print_tokens_between(beg, end):
        assert beg <= end
        for n in range(beg, end):
            print(f"{n}: {processor.decode(n).__repr__()}")

    print_tokens_between(0, 70)
    assert len(processor) > 1005
    print_tokens_between(1000, 1005)
    print_tokens_between(len(processor) - 10, len(processor))


if __name__ == "__main__":
    main()
