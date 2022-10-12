def render_template(template_path: str, **kwargs):
    with open(template_path) as fp:
        text = fp.read().format(**kwargs)
        return text
