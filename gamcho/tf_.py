# Do NOT import tensorflow here directly, to run with user's package
# TODO Add tf version check for each helper
# TODO Suppress warning
# TODO Test with other tensorflow version
# TODO Useful helper
# - name scopes as directory view
# - count number of node
import logging
from pathlib import Path

from google.protobuf.json_format import MessageToJson


def guess_output_ops(graph):
    """
    Generator for the graph output operation candidates
    """
    for op in graph.get_operations():
        # Check type blacklist
        # TODO Update blacklist
        if op.type in ('Assign'):
            continue

        # Check no consumer
        if any([output.consumers() for output in op.outputs]):
            continue

        yield op


def dump_graph_def_json(graph, *, path=Path.home() / 'buffer.graphdef.json'):
    path = Path(path)
    assert path.suffix == '.json'

    graph_def = graph.as_graph_def(add_shapes=False)
    # 'add_shapes=True' might be useful, with shape inference?

    with open(path, mode='w') as f:
        f.write(MessageToJson(graph_def, indent=2))


def dump_full_graph_pb(graph, *, path=Path.home() / 'buffer.full.pb'):
    path = Path(path)
    assert path.suffix == '.pb'

    graph_def = graph.as_graph_def()
    with open(path, mode='wb') as f:
        f.write(graph_def.SerializeToString())


def dump_frozen_graph_pb(tf, graph, *, outputs=None, path=Path.home() / 'buffer.frozen.pb'):
    """
    Compatibility:
    - tested on TF 1.15

    Args:
    - tf: User's tensorflow module
        TODO Take tf context, not passing tf module
    - outputs: List of graph output, guess for None
        Supported types: str, tf.Tensor, tf.Operation
    """
    path = Path(path)
    assert path.suffix == '.pb'

    def get_op_name(arg):
        if isinstance(arg, str):
            # This will throw on no match
            graph.get_operation_by_name(arg)
            return arg

        if isinstance(arg, tf.Operation):
            return arg.name

        if isinstance(arg, tf.Tensor):
            return arg.op.name

        raise RuntimeError(f'Unsupported type: {type(arg)}')

    if outputs is None:
        output_names = [op.name for op in guess_output_ops(graph)]
    else:
        output_names = [get_op_name(output) for output in outputs]

    assert output_names
    assert all([isinstance(name, str) for name in output_names])

    # TODO Does it make difference when add_shapes=True?
    graph_def = graph.as_graph_def(add_shapes=False)

    with tf.Session(graph=graph, config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        sess.run(tf.initializers.global_variables())

        frozen_graph_def = tf.graph_util.convert_variables_to_constants(
            sess, graph_def, output_names)

        with open(path, mode='wb') as f:
            f.write(frozen_graph_def.SerializeToString())


def dump_tflite(tf, graph, *, inputs, outputs=None, path=Path.home() / 'buffer.tflite'):
    """
    Compatibility:
    - tested on TF 1.15

    Args:
    - tf: User's tensorflow module
        TODO Take tf context, not passing tf module
    - inputs/outputs: List of graph inputs/output, guess for None
        Supported types: str, tf.Tensor, tf.Operation
    """
    path = Path(path)
    assert path.suffix == '.pb'

    assert inputs is not None  # TODO Can we guess?

    def get_tensor(arg):
        if isinstance(arg, tf.Tensor):
            return arg

        if isinstance(arg, str):
            if ':' in arg:
                return graph.get_tensor_by_name(arg)

            arg = graph.get_operation_by_name(arg)

        if isinstance(arg, tf.Operation):
            # TODO Consider multi-output op
            assert len(arg.outputs) == 1
            return arg.outputs[0]

        raise RuntimeError(f'Unsupported type: {type(arg)}')

    if outputs is None:
        output_tensors = [get_tensor(op) for op in guess_output_ops(graph)]
    else:
        output_tensors = [get_tensor(output) for output in outputs]

    assert output_tensors
    assert all([isinstance(name, tf.Tensor) for name in output_tensors])

    input_tensors = [get_tensor(input_) for input_ in inputs]

    # Q. `input_tensors` as empty list possible?
    assert input_tensors
    assert all([isinstance(name, tf.Tensor) for name in input_tensors])

    with tf.Session(graph=graph, config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        sess.run(tf.initializers.global_variables())

        def get_converter_cls():
            if hasattr(tf, 'compat') and hasattr(tf.compat, 'v1'):
                # Only v1 converter has `from_session`, no v2
                return tf.compat.v1.lite.TFLiteConverter

            logging.warn('Using unknown version of TFLiteConverter, while designed for v1')
            return tf.lite.TFLiteConverter

        TFLC = get_converter_cls()
        converter = TFLC.from_session(sess, input_tensors, output_tensors)

        with open(path, "wb") as f:
            f.write(converter.convert())
