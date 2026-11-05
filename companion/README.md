# The Tonmick files

These are the files the three programs read. They are a small part of the Predictive companion, https://github.com/nicholaskarlson/predict, release v1.0.1 (commit `24d1023f00e6eb1e4790e749b287ea9a9133b3aa`). Each file is copied byte for byte and kept at the companion's own path, so the programs read them exactly as they would read the companion.

| File | What it is |
| --- | --- |
| `.../tonmick-v1.0.0/data/anchor/participants.csv` | All 1,600 invited students: college, part-time and first-in-family status, entry grade, design weights, and whether the student joined |
| `.../tonmick-v1.0.0/data/anchor/baseline.csv` | The 1,219 students who joined: the offer of mentoring, sessions attended, how they answered the entry survey, and their answers |
| `.../tonmick-v1.0.0/data/anchor/registry.csv` | The college records: withdrawal, transfer, grades, and support visits |
| `.../tonmick-observed-v1.1.0/data/anchor_observed_registry.csv` | Withdrawal within the year for all 1,600 invited students, including those who did not join |
| `DICTIONARY.csv` (in each folder) | What every column means |
| `.../tonmick-v1.0.0/WORLD_SPEC.md` | The rules that made the data, which the book cites when it compares an estimate with the truth |
| `PROVENANCE.*`, `OBSERVATION_POLICY.md`, `LICENSES.md` | Where the files came from, how the observed registry was drawn, and their licenses |

`SHA256SUMS` lists these files with the checksums from the companion's own `SHA256SUMS`, line for line. From this folder, `sha256sum -c SHA256SUMS` (Linux) or `shasum -a 256 -c SHA256SUMS` (macOS) confirms them.

The data are synthetic. They describe no real student.
