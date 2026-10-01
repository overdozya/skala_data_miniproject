# Data layout

`raw/` contains the original MATLAB files downloaded from the public source. It is
kept out of Git because the files are several gigabytes each. `processed/` contains
tables extracted by the local analysis script. The analysis uses one row per cell
for cross-cell statistics and early-cycle features; cycle-level records are kept
separate so that late-life measurements cannot enter early prediction features.

Source: https://data.matr.io/1/projects/5c48dd2bc625d700019f3204

This assignment uses `2017-05-12` (Batch 1), `2018-02-20` (Batch 2), and
`2018-04-12` (Batch 3). The `2018-04-03 varcharge` file is stored in `raw/extra/`
and excluded from the DAY 1 analysis. The source author's lifetime-prediction
code instead uses `2017-06-30` as its second batch; see the root README for why
the published 9.1% error is a reference rather than an identical split.


hi hello