import jinja2
from pathlib import Path


def render(template_path, **kwargs):
    parent_path = Path(template_path).parent
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=parent_path), autoescape=True)
    template = env.get_template(Path(template_path).name)
    return template.render(**kwargs)
