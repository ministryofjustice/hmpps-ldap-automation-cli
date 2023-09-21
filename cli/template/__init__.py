import os.path

import jinja2
from pathlib import Path


def render(template_path, **kwargs):
    parent_path = Path(template_path).parent
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(searchpath=parent_path), autoescape=True
    )
    template = env.get_template(Path(template_path).name)
    return template.render(**kwargs)


def save(rendered_text, template_path, rendered_dir="./rendered/"):
    # create rendered_dir if it doesn't exist
    if not Path.exists(Path(rendered_dir)):
        Path.mkdir(Path(rendered_dir))
    # create the directory structure for the template file if it doesn't exist
    if not Path.exists(Path(os.path.join(rendered_dir, template_path)).parent):
        Path.mkdir(Path(os.path.join(rendered_dir, template_path)).parent)
    file = Path(os.path.join(rendered_dir, template_path.replace(".j2", "")))
    file.touch(exist_ok=True)
    file.write_text(rendered_text)
    return file
