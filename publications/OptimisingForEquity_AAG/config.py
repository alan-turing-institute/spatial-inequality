import yaml


def get_config():
    with open("config.yml") as f:
        return yaml.safe_load(f)


config = get_config()
