from pathlib import Path

import click
import sentencepiece as spm


def check_conjecture(processor: spm.SentencePieceProcessor):
    # Version(?) check
    assert processor.get_encoder_version() == 0

    # Size check
    size = len(processor)
    assert size == processor.get_piece_size()
    assert size == processor.vocab_size()
    assert size == processor.piece_size()


@click.group()
def cli():
    pass


@cli.command()
@click.argument('spm_model_path')
def inspect(spm_model_path):
    spm_model_path = Path(spm_model_path)
    assert spm_model_path.is_file()

    processor = spm.SentencePieceProcessor(str(spm_model_path))
    check_conjecture(processor)
    print(f"length of processor: {len(processor)}")

    print(f"unk id: {processor.unk_id()}")
    print(f"bos id: {processor.bos_id()}")
    print(f"eos id: {processor.eos_id()}")
    print(f"pad id: {processor.pad_id()}")

    # TODO This makes too long output. Let's make tabular.
    def print_pieces_between(beg, end):
        assert beg <= end
        for n in range(beg, end):
            print(f"{n}: {processor.id_to_piece(n)}")

    print_pieces_between(0, 70)
    assert len(processor) > 1005
    print_pieces_between(1000, 1005)
    print_pieces_between(len(processor) - 10, len(processor))


if __name__ == "__main__":
    cli()
