#!/usr/bin/env python3
"""Plot independent Lint/detekt/UI scores, grouped by metric rather than candidate."""
import argparse
import json
import math
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def score(value, label):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Missing or invalid score: ' + label)
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ValueError('Score must be finite and between 0 and 100: ' + label)
    return number


def load_chart(filename):
    filename = Path(filename).resolve()
    config = read(filename)
    candidates = config['candidates']
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError('At least two candidates are required')
    ui = read(filename.parent / config['ui_result']) if config.get('ui_result') else None
    # Accept both raw UI result files and evidence wrappers retaining the original result.
    if ui is not None:
        ui = ui.get('result', ui)
        if not isinstance(ui.get('method'), str) or not ui['method'].strip():
            raise ValueError('UI result must describe its scoring method')
    names, files, rows = set(), set(), []
    for candidate in candidates:
        name = candidate['name']
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError('Candidate names must be nonempty and unique')
        names.add(name)
        path = (filename.parent / candidate['score_file']).resolve()
        if path in files:
            raise ValueError('Each candidate needs its own score result file')
        files.add(path)
        result = read(path)
        if result.get('schema_version') != 14 or result.get('publication_status') != 'complete':
            raise ValueError('Only complete v14 score results can be charted: ' + name)
        if rows and result['manifest_sha256'] != rows[0]['manifest_sha256']:
            raise ValueError('Candidates must share the same frozen scoring manifest')
        values = [score(result['analyzer_scores'][tool]['score'], name + '/' + tool)
                  for tool in ('android-lint', 'detekt')]
        if ui is not None:
            values.append(score(ui['scores'][candidate['ui_key']], name + '/UI'))
        rows.append({'name': name, 'values': values, 'manifest_sha256': result['manifest_sha256']})
    return config, rows, ui


def render(config, rows, ui, output, formats, font=None):
    # Charting is optional: scoring/verification and their imports remain standard-library-only.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError as error:
        raise ValueError('Chart export requires matplotlib in this Python environment (python3 -m pip install matplotlib)') from error
    if font:
        candidates = [Path(font)]
    else:
        candidates = [Path(p) for p in ('/System/Library/Fonts/PingFang.ttc',
                      '/System/Library/Fonts/STHeiti Light.ttc',
                      '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
    for path in candidates:
        if path.is_file():
            font_manager.fontManager.addfont(str(path))
            plt.rcParams['font.family'] = font_manager.FontProperties(fname=path).get_name()
            break
    else:
        if font:
            raise ValueError('Font file does not exist: ' + font)
    plt.rcParams['axes.unicode_minus'] = False
    labels = ['Lint', 'detekt'] + ([config.get('ui_label', 'UI 还原（SSIM）')] if ui else [])
    fig, ax = plt.subplots(figsize=(11, 6.4), facecolor='#F7F9FC')
    ax.set_facecolor('#F7F9FC')
    colors = ['#3885CF', '#35A98A', '#E9A142', '#9673C3', '#D16E83', '#56A5AD']
    width = .72 / len(rows)
    for index, row in enumerate(rows):
        positions = [x + (index - (len(rows) - 1) / 2) * width for x in range(len(labels))]
        bars = ax.bar(positions, row['values'], width, label=row['name'],
                      color=colors[index % len(colors)], zorder=3)
        ax.bar_label(bars, labels=[f'{v:.2f}'.rstrip('0').rstrip('.') for v in row['values']],
                     padding=6, fontsize=12, color='#243348')
    ax.set_ylim(0, 110)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel('分数（满分 100）', fontsize=11)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=12)
    ax.tick_params(axis='both', length=0, pad=10, colors='#475569')
    ax.grid(axis='y', color='#DDE3ED', linewidth=.8, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.suptitle(config.get('title', '实现方案评分对比'), fontsize=21, fontweight='bold',
                 x=.08, ha='left', y=.97, color='#182A42')
    subtitle = 'Lint / detekt：v14 扣分制'
    if ui:
        subtitle += '    ·    ' + config.get('ui_note', ui['method'])
    ax.set_title(subtitle, fontsize=11, color='#64748B', loc='left', pad=44)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.055), ncol=min(3, len(rows)), frameon=False, fontsize=11)
    note = '三项独立计分，不计算综合分。' if ui else '两项独立计分，不计算综合分。'
    if ui:
        note = 'UI 为图像相似度，不代表人工验收；' + note
    fig.text(.08, .035, note, fontsize=10, color='#64748B')
    fig.subplots_adjust(left=.08, right=.98, bottom=.15, top=.78)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = [Path(str(output) + '.' + extension) for extension in formats]
    for path in paths:
        fig.savefig(path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', help='Chart JSON; paths resolve relative to this file, candidate order is preserved')
    parser.add_argument('--out-prefix', required=True, help='Output filename prefix without an extension')
    parser.add_argument('--format', nargs='+', choices=('png', 'svg'), default=['png', 'svg'])
    parser.add_argument('--font', help='Optional font file supporting the chart labels')
    args = parser.parse_args()
    try:
        config, rows, ui = load_chart(args.config)
        paths = render(config, rows, ui, args.out_prefix, args.format, args.font)
        print(json.dumps({'outputs': [str(p) for p in paths], 'candidates': [r['name'] for r in rows]}, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, 'Cannot export score chart: ' + str(error) + '\n')


if __name__ == '__main__':
    sys.exit(main())
