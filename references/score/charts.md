# Score comparison charts

Run chart export only when a visualization is requested. It reads complete v14 analyzer score results and optional UI results; it does not run analyzers, repair code or calculate a combined grade.

```sh
compose-quality chart chart.json --out-prefix reports/score-comparison
# Or from a source checkout:
python3 scripts/score/chart.py chart.json --out-prefix reports/score-comparison
```

The default outputs are PNG (200 dpi) and SVG. Use `--format svg` or `--format png` to choose one. Chart export requires matplotlib in the executing Python environment; other CLI commands remain standard-library-only. If needed, install it in the intended environment with `python3 -m pip install matplotlib`. No dependency installation happens automatically. Use `--font /path/to/font.ttf` for labels unsupported by installed fonts; common macOS Chinese and Linux Noto CJK font locations are detected automatically.

Example chart configuration (all input paths resolve relative to chart.json):

```json
{
  "title": "三种实现方案评分对比",
  "ui_result": "ui/result.json",
  "ui_label": "UI 还原（SSIM）",
  "ui_note": "UI：31 状态等权 SSIM × 100",
  "candidates": [
    {"name": "仅 Figma", "score_file": "baseline/score.json", "ui_key": "baseline"},
    {"name": "Figma + Chris Banes", "score_file": "chris-banes/score.json", "ui_key": "chris-banes"},
    {"name": "Figma + Compose Coder", "score_file": "compose-coder/score.json", "ui_key": "compose-coder"}
  ]
}
```

The UI input is an evidence result containing `method` and `scores`, for example `{"method":"RGB SSIM × 100", "scores":{"baseline":55.34,"chris-banes":52.96,"compose-coder":63.84}}`. A reuse receipt wrapping that object under `result` is also accepted. Link real evidence instead of filling manual UI grades. The caller must verify image/source identity and disclose reused UI evidence before publishing. Omit `ui_result`, `ui_note`, `ui_label` and candidate `ui_key` fields for a two-metric static chart.

Each metric forms one group; candidate order controls bar/legend order. Use concrete scenario names and the order requested by the user. The export rejects incomplete/non-v14 results, different scoring manifests, duplicate candidate names/result paths and missing/nonfinite/out-of-range scores. It preserves warning/error scores and does not turn a high numeric score into a passed gate. UI image similarity is displayed separately from static deductions and is not human acceptance.
