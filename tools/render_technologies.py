"""Regenerate the technology layout after editing assets/technologies.json.

Run: python tools/render_technologies.py
Icon sources are cached locally; only new icons require a download.
"""
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def render():
    categories = json.loads((ASSETS / 'technologies.json').read_text(encoding='utf-8'))
    cache = ASSETS / 'technology-icons'
    cache.mkdir(parents=True, exist_ok=True)
    width, row_height, label_width, size = 1000, 86, 180, 48
    height = len(categories) * row_height
    for theme, color in [('dark', '#e6edf3'), ('light', '#1f2328')]:
        svg = ET.Element(f'{{{NS}}}svg', {'viewBox': f'0 0 {width} {height}', 'width': str(width), 'height': str(height), 'role': 'img', 'aria-labelledby': 'title desc'})
        ET.SubElement(svg, f'{{{NS}}}title', {'id': 'title'}).text = 'Tecnologías de Nestor Hernández Díaz'
        ET.SubElement(svg, f'{{{NS}}}desc', {'id': 'desc'}).text = '; '.join(c['category'] + ': ' + ', '.join(i['name'] for i in c['icons']) for c in categories)
        border = '#30363d' if theme == 'dark' else '#d1d9e0'
        frame = ET.SubElement(svg, f'{{{NS}}}g', {'fill': 'none', 'stroke': border, 'stroke-width': '1'})
        ET.SubElement(frame, f'{{{NS}}}rect', {'x': '.5', 'y': '.5', 'width': str(width - 1), 'height': str(height - 1)})
        ET.SubElement(frame, f'{{{NS}}}path', {'d': f'M {label_width} 0 V {height}'})
        for row in range(1, len(categories)):
            ET.SubElement(frame, f'{{{NS}}}path', {'d': f'M 0 {row * row_height} H {width}'})
        for row, category in enumerate(categories):
            icons = category['icons']
            assert icons, 'Each category needs at least one icon'
            slot = (width - label_width) / len(icons)
            icon_size = min(size, slot - 16)
            assert icon_size > 0, 'Too many icons for one row'
            label = ET.SubElement(svg, f'{{{NS}}}text', {'x': '12', 'y': str(row * row_height + row_height / 2 + 6), 'fill': color, 'font-family': 'Segoe UI, sans-serif', 'font-size': '17', 'font-weight': '600'})
            label.text = category['category']
            for column, icon in enumerate(icons):
                path = cache / (icon['id'] + '.svg')
                if not path.exists():
                    request = urllib.request.Request(icon['url'], headers={'User-Agent': 'GitHub-profile-assets/1.0'})
                    with urllib.request.urlopen(request, timeout=30) as response:
                        source = response.read()
                    ET.fromstring(source)
                    path.write_bytes(source)
                source = ET.fromstring(path.read_bytes())
                # Inline class rules so different source icons cannot override
                # one another through shared class names such as cls-1.
                rules = {}
                for style in source.iter(f'{{{NS}}}style'):
                    for selectors, declarations in re.findall(r'([^{}]+)\{([^{}]+)\}', style.text or ''):
                        properties = dict(item.strip().split(':', 1) for item in declarations.split(';') if ':' in item)
                        for selector in selectors.split(','):
                            selector = selector.strip()
                            if selector.startswith('.'):
                                rules[selector[1:]] = properties
                for element in source.iter():
                    for class_name in element.attrib.get('class', '').split():
                        for name, value in rules.get(class_name, {}).items():
                            element.set(name.strip(), value.strip())
                    element.attrib.pop('class', None)
                for parent in source.iter():
                    for child in list(parent):
                        if child.tag == f'{{{NS}}}style':
                            parent.remove(child)
                # Scope gradient, mask and clip identifiers to this icon instance.
                prefix = f'icon-{row}-{column}-'
                ids = {e.attrib['id']: prefix + e.attrib['id'] for e in source.iter() if 'id' in e.attrib}
                for element in source.iter():
                    for key, value in list(element.attrib.items()):
                        if key == 'id':
                            element.set(key, ids[value])
                        else:
                            value = value.replace('data:img/png;', 'data:image/png;')
                            for old, new in ids.items():
                                value = value.replace(f'url(#{old})', f'url(#{new})')
                                if value == '#' + old:
                                    value = '#' + new
                            element.set(key, value)
                x = label_width + (column + .5) * slot - icon_size / 2
                y = row * row_height + (row_height - icon_size) / 2
                source.set('x', f'{x:.2f}')
                source.set('y', f'{y:.2f}')
                source.set('width', f'{icon_size:.2f}')
                source.set('height', f'{icon_size:.2f}')
                ET.SubElement(source, f'{{{NS}}}title').text = icon['name']
                svg.append(source)
        ET.ElementTree(svg).write(ASSETS / f'technologies-{theme}.svg', encoding='utf-8', xml_declaration=True)
    print(f'Rendered {sum(len(c["icons"]) for c in categories)} icons in {len(categories)} categories; no tables or external image dependencies.')


if __name__ == '__main__':
    render()
