from pathlib import Path

import click
import yaml
import sentencepiece as spm
import linecache


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


@cli.command()
@click.option("--spm_model_path", help="Ingredient spm model binary file")
@click.option("--vocab_path", help="Vocabruary file name to generate. (Supported suffix: .yml)")
def extract_vocab(spm_model_path, vocab_path):
    spm_model_path = Path(spm_model_path)
    assert spm_model_path.is_file()

    vocab_path = Path(vocab_path)
    assert vocab_path.parent.is_dir()
    assert vocab_path.suffix == ".yml"  # TODO Support other

    processor = spm.SentencePieceProcessor(str(spm_model_path))
    check_conjecture(processor)

    vocab_dict = {}

    for n in range(len(processor)):
        vocab_dict[processor.id_to_piece(n)] = n

    with open(vocab_path, 'w') as vocab_file:
        yaml.safe_dump(vocab_dict, stream=vocab_file, allow_unicode=True, sort_keys=False)


@cli.command()
@click.option("--spm_model_path", required=True)
@click.option("--corpus_path", required=True, help="Corpus with each sentence split by line")
def report_longest_line(spm_model_path, corpus_path):
    spm_model_path = Path(spm_model_path)
    assert spm_model_path.is_file()

    corpus_path = Path(corpus_path)
    assert corpus_path.is_file()

    processor = spm.SentencePieceProcessor(str(spm_model_path))

    with open(corpus_path) as corpus_file:
        token_count_by_line = []

        for line in corpus_file:
            token_count_by_line.append(len(processor.Encode(line)))

        # argmax
        max_idx = max(range(len(token_count_by_line)), key=lambda x: token_count_by_line[x])

    max_token_count = token_count_by_line[max_idx]
    max_sent = linecache.getline(str(corpus_path), max_idx + 1)  # lineno = index + 1
    max_sent_tokenized = processor.encode(max_sent, out_type=str)

    print(f"- INDEX: {max_idx}")
    print(f"- COUNT: {max_token_count}")
    print("- SENTENCE:")
    print(f"{max_sent}", end="")
    print("- SENTENCE(TOKENIZED):")
    print(f"{max_sent_tokenized}")


if __name__ == "__main__":
    cli()
