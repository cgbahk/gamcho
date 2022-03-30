# Do NOT import tensorflow here directly, to run with user's package
# TODO Add tf version check for each helper
# TODO Suppress warning
# TODO Test with other tensorflow version
# TODO Useful helper
# - name scopes as directory view
# - count number of node
# TODO Test this!
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


class TensorResolver:
    # TODO Manage exceptions
    """
    Syntactic sugar to find tf.Tensor

    How to use:
        find_tensor = TensorResolver(tf)
        ... = find_tensor.of(graph).by(arg)

    Supported types for arg: str, tf.Tensor, tf.Operation
    """

    def __init__(self, tf):
        self._tf = tf

    def of(self, graph):
        assert isinstance(graph, self._tf.Graph)

        def _find_tensor(arg):
            if isinstance(arg, self._tf.Tensor):
                assert arg.graph == graph
                return arg

            if isinstance(arg, str):
                if ':' in arg:
                    return graph.get_tensor_by_name(arg)

                arg = graph.get_operation_by_name(arg)

            if isinstance(arg, self._tf.Operation):
                assert arg.graph == graph
                # TODO Consider multi-output op
                assert len(arg.outputs) == 1
                return arg.outputs[0]

            raise RuntimeError(f'Unsupported type: {type(arg)}')

        class _Query:
            pass

        query = _Query()
        query.by = _find_tensor

        return query


def dump_graph_def_json(graph, *, path=Path.home() / 'buffer.graphdef.json'):
    path = Path(path)
    assert path.suffix == '.json'

    graph_def = graph.as_graph_def(add_shapes=False)
    # 'add_shapes=True' might be useful, with shape inference?

    with open(path, mode='w') as f:
        f.write(MessageToJson(graph_def, indent=2))


def dump_pb(graph, *, path=Path.home() / 'buffer.pb'):
    path = Path(path)
    assert path.suffix == '.pb'

    graph_def = graph.as_graph_def()
    with open(path, mode='wb') as f:
        f.write(graph_def.SerializeToString())


def freeze(tf, graph, *, outputs=None):
    # TODO Support inputs
    """
    Compatibility:
    - tested on TF 1.15

    Args:
    - tf: User's tensorflow module
        TODO Take tf context, not passing tf module
    - outputs: List of graph output, guess for None
        Supported types: str, tf.Tensor, tf.Operation

    Returns: tf.Graph, frozen graph, preserve names
    """

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
            sess, graph_def, output_names
        )

        with tf.Graph().as_default() as ret_graph:
            tf.graph_util.import_graph_def(frozen_graph_def, name='')

            return ret_graph


def dump_tflite(tf, graph, *, inputs, outputs=None, path=Path.home() / 'buffer.tflite'):
    # TODO Take how to fill unknown shape
    # TODO Error occurs when insufficient inputs provided, error message is not kind
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
    assert path.suffix == '.tflite'

    assert inputs is not None  # TODO Can we guess?

    find_tensor = TensorResolver(tf)

    if outputs is None:
        outputs = guess_output_ops(graph)

    orig_input_tensors = [find_tensor.of(graph).by(input_) for input_ in inputs]
    orig_output_tensors = [find_tensor.of(graph).by(output) for output in outputs]

    frozen_graph = freeze(tf, graph, outputs=orig_output_tensors)

    def resolve_unknown_shape(tensor_shape):
        resolved_shape_list = [1 if dim is None else dim for dim in tensor_shape.as_list()]

        ret = tf.TensorShape(resolved_shape_list)
        ret.assert_is_fully_defined()

        return ret

    # Replace input with placeholder
    with tf.Graph().as_default() as new_graph:
        input_map = {}

        for orig_input_tensor in orig_input_tensors:
            new_source = tf.placeholder(orig_input_tensor.dtype, name=orig_input_tensor.op.name)

            # TODO Can I use 'tf.ensure_shape'?
            new_source.set_shape(resolve_unknown_shape(orig_input_tensor.shape))

            input_map[orig_input_tensor.name] = new_source

        tf.graph_util.import_graph_def(frozen_graph.as_graph_def(), input_map=input_map, name='')

    new_input_tensors = list(input_map.values())
    new_output_tensors = [
        find_tensor.of(new_graph).by(output.name) for output in orig_output_tensors
    ]
    with tf.Session(graph=new_graph, config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        # Note variable initialization not required as graph frozen

        def get_converter_cls():
            if hasattr(tf, 'compat') and hasattr(tf.compat, 'v1'):
                # Only v1 converter has `from_session`, no v2
                return tf.compat.v1.lite.TFLiteConverter

            logging.warn('Using unknown version of TFLiteConverter, while designed for v1')
            return tf.lite.TFLiteConverter

        TFLC = get_converter_cls()
        # TODO Consider 'from_frozen_graph'? But if is from file...
        converter = TFLC.from_session(sess, new_input_tensors, new_output_tensors)

        # TODO Verify effect of this feature
        # Ref: https://www.tensorflow.org/lite/guide/ops_select
        converter.target_spec.supported_ops = [
            tf.lite.OpsSet.TFLITE_BUILTINS,  # enable TensorFlow Lite ops (default)
            tf.lite.OpsSet.SELECT_TF_OPS,  # enable additional TensorFlow ops
        ]

        tflite_model_content = converter.convert()
        with open(path, "wb") as f:
            f.write(tflite_model_content)
