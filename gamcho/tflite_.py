import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import tflite


def get_model(tflite_path):
    assert tflite_path.is_file()

    with open(tflite_path, 'rb') as tflite_file:
        return tflite.Model.GetRootAsModel(tflite_file.read(), 0)


def get_opstat_frame(model: tflite.Model, graph_index: int):
    assert graph_index < model.SubgraphsLength()
    graph = model.Subgraphs(graph_index)

    opcode_order = []
    for i in range(graph.OperatorsLength()):
        op = graph.Operators(i)
        opcode = model.OperatorCodes(op.OpcodeIndex())
        opcode_order.append(opcode.BuiltinCode())

    op_codes, op_counts = np.unique(opcode_order, return_counts=True)

    df = pd.DataFrame({
        'CODE': op_codes,
        'COUNT': op_counts,
    })
    df = df.sort_values(by='COUNT', ascending=False)

    df['OPNAME'] = df['CODE'].apply(tflite.utils.opcode2name)

    return df[['COUNT', 'OPNAME']].set_index('OPNAME')


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('tflite_path')
    args = parser.parse_args()

    tflite_path = Path(args.tflite_path)
    model = get_model(tflite_path)

    print(f'Model: {tflite_path}')

    for i in range(model.SubgraphsLength()):
        opstat_frame = get_opstat_frame(model, i)
        print(f'Subgraph {i}')
        print(opstat_frame.to_markdown())


if __name__ == '__main__':
    main()
