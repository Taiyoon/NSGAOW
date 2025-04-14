from copy import deepcopy
from typing import Callable, List,  Dict, TypeGuard
from pprint import pprint
import yaml  # type: ignore
import numpy as np
from typing import Any, Dict, Union


ConfigValue = str | int | float | List[int]
UnparsedConfig = Dict[str, Union["Config", "UnparsedConfig"]
                      ] | List["Config"] | List["UnparsedConfig"] | ConfigValue
Config = Dict[str, Union["Config"]] | List["Config"] | ConfigValue


def is_unparsed_config(x: Any) -> TypeGuard[UnparsedConfig]:
    if isinstance(x, dict):
        for key, value in x.items():
            if not isinstance(key, str):
                return False
            if not (isinstance(value, (str, int, float)) or is_unparsed_config(value)):
                return False
        return True
    elif isinstance(x, list):
        return all(is_unparsed_config(item) for item in x)
    else:
        return False


def is_config(x: Any) -> TypeGuard[Config]:
    raise NotImplementedError


class ConfigParser:
    def __init__(self, config_path: str, rng: np.random.Generator = np.random.default_rng()):
        self.rng = rng
        self.unparsed_config = self._load_config(config_path)
        if isinstance(self.unparsed_config, list):
            config = self.unparsed_config
            self.config = {}
            for c in config:
                assert len(c) == 1
                (k, v), = list(c.items())
                self.config[k] = self._parse(deepcopy(v))
        else:
            self.config = self._parse(deepcopy(self.unparsed_config))
        

    @staticmethod
    def _load_config(path: str) -> UnparsedConfig:
        """加载并预处理YAML配置文件"""
        with open(path) as f:
            # 启用FullLoader以支持YAML锚点
            res = yaml.load(f, Loader=yaml.FullLoader)
            assert isinstance(res, Dict | List)
            return res

    def no_replace_integers(self, low: int, high: int, size: int) -> List[int]:
        val = self.rng.choice(range(low, high), size, replace=False)
        return list(val)

    # custom distribution
    def bounded_zipf(self, high: int, a: float) -> int:
        val = self.rng.zipf(a)
        while val >= high:
            val = self.rng.zipf(a)
        return val - 1

    DISTRIBUTE_DICT: Dict[str, Callable[..., ConfigValue]] = {
        'no_replace_integers': no_replace_integers,
        'bounded_zipf': bounded_zipf
    }

    def _handle_distribution(self, u_conf: Dict[str, UnparsedConfig]) -> ConfigValue:
        distribution: Dict[str, UnparsedConfig] = u_conf.pop(
            "distribution")  # type: ignore
        assert isinstance(distribution, dict)
        for k, v in distribution.items():
            if isinstance(v, dict):
                assert "distribution" in v and len(v) == 1
                distribution[k] = self._handle_distribution(v)
        method = distribution.pop('method')
        assert isinstance(method, str)
        if method in self.DISTRIBUTE_DICT:
            f = self.DISTRIBUTE_DICT[method]
            return f(self, **distribution)
        else:
            v = getattr(self.rng, method)(**distribution)
            # HACK
            return v    # type: ignore

    def _parse(self, u_conf: UnparsedConfig) -> Config:
        conf: Config
        if isinstance(u_conf, dict):
            if "repeat" in u_conf:
                repeat = u_conf.pop("repeat")
                assert isinstance(repeat, int)  # assert 在这里推荐吗?
                conf = []
                for _ in range(repeat):
                    v = self._parse(deepcopy(u_conf))
                    conf.append(v)  # type: ignore
            elif "distribution" in u_conf:
                conf = self._handle_distribution(u_conf)
            else:
                conf = {}
                for k, v in u_conf.items():
                    if is_unparsed_config(v):
                        conf[k] = self._parse(v)
                    else:
                        conf[k] = v
                    assert not ("repeat" in conf or "distribution" in conf)
        elif isinstance(u_conf, list):
            conf = []
            for t in u_conf:
                parsed_t = self._parse(t)
                if isinstance(parsed_t, list):
                    conf += parsed_t
                # 是环境
                elif isinstance(parsed_t, dict) and len(parsed_t) == 1 and 'cloud' in list(parsed_t.values())[0]:
                    conf.append(parsed_t)
                else:
                    raise ValueError(t)
        else:
            raise ValueError(f'Cannot parse {u_conf}')
        return conf


if __name__ == "__main__":
    CONFIG_FILE = "config/task_amount.yml"
    parser = ConfigParser(CONFIG_FILE)
    pprint(parser.config)


