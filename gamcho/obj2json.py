from pathlib import Path
import json
import logging

TYPE_HINT_KEY = "__type_hint_by_gamcho"

LOGGER = logging.getLogger(__name__)


class Serializer:
    fullname: str = None  # {module}.{qualname}

    def serialize_with_type_hint(self, obj):
        ret = {TYPE_HINT_KEY: self.fullname}

        raw_obj_dict = self.serialize(obj)
        assert isinstance(raw_obj_dict, dict)
        assert TYPE_HINT_KEY not in raw_obj_dict

        ret.update(raw_obj_dict)

        return ret

    def serialize(self, obj):
        """Return dict that represents obj data"""
        raise NotImplementedError


SERIALIZER_REGISTRY = {}  # { fullname: serializer, ... }


def register(fullname: str):

    def decorator(orig_class):
        orig_class.fullname = fullname

        # TODO Check duplication
        SERIALIZER_REGISTRY[fullname] = orig_class
        return orig_class

    return decorator


@register("omegaconf.dictconfig.DictConfig")
class OmegaDictConfig_Serializer(Serializer):

    def serialize(self, obj):
        import omegaconf
        return omegaconf.OmegaConf.to_container(obj)


@register("argparse.Namespace")
class ArgparseNamespace_Serializer(Serializer):

    def serialize(self, obj):
        return vars(obj)


class ManyEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            pass

        obj_type_fullname = f"{type(obj).__module__}.{type(obj).__qualname__}"

        if obj_type_fullname in SERIALIZER_REGISTRY:
            serializer = SERIALIZER_REGISTRY[obj_type_fullname]()
            return serializer.serialize_with_type_hint(obj)

        fallback_ret = f"<{obj_type_fullname}> (Not yet serializable by gamcho)"
        LOGGER.warning(fallback_ret)  # TODO Log once per type
        return fallback_ret


def dump(obj, *, json_path):
    json_path = Path(json_path)
    with open(json_path, "w") as json_file:
        json.dump(
            obj,
            json_file,
            indent=2,
            cls=ManyEncoder,
        )


if __name__ == "__main__":
    pass
