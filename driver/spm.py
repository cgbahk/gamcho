from pathlib import Path

import click
import sentencepiece as spm


@click.group()
def cli():
    pass


@cli.command()
@click.argument('spm_model_path')
def inspect(spm_model_path):
    spm_model_path = Path(spm_model_path)
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
    cli()
