import yaml
from omegaconf import OmegaConf


def save_yaml(data, save_name):
    """
    Save the dictionary into a yaml file.

    Parameters
    ----------
    data : dict
        The dictionary contains all data.

    save_name : string
        Full path of the output yaml file.
    """
    if isinstance(data, dict):
        with open(save_name, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
    else:
        with open(save_name, "w") as f:
            OmegaConf.save(data, f)

import yaml, re

def parse_yaml(file: str) -> dict:
    """
    Load a YAML file (scientific-safe).
    Returns dict.
    """
    with open(file, "r") as stream:
        loader = yaml.SafeLoader
        loader.add_implicit_resolver(
            u'tag:yaml.org,2002:float',
            re.compile(u'''^(?:
             [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
            |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
            |\\.[0-9_]+(?:[eE][-+][0-9]+)?
            |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
            |[-+]?\\.(?:inf|Inf|INF)
            |\\.(?:nan|NaN|NAN))$''', re.X),
            list(u'-+0123456789.')
        )
        return yaml.load(stream, Loader=loader)
