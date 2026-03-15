# Curator Guide — Twi Text Collection

---

## Repo Structure

```
twi-text-collector/
├── collector.py              ← volunteers run this
├── README.md                 ← volunteer instructions
├── .gitignore
└── scripts/
    ├── CURATOR_README.md     ← you are here
    └── generate_codes.py     ← generate volunteer codes
```

Private files (never commit):
```
volunteer_codes.json          ← all codes + assigned indices
collector_config.json         ← auto-created by volunteers locally
texts_<hash>/                 ← volunteer's local texts
```

HuggingFace repos:
```
ghananlpcommunity/twi-english-paragraph-dataset_news  ← input (English paragraphs)
ghananlpcommunity/prestine-twi                         ← output (Twi texts)
```

---

## Generate Volunteer Codes

Open `scripts/generate_codes.py` and configure:

```python
TOTAL_PARAGRAPHS = 257000           # Total in dataset
PARAGRAPHS_PER_VOLUNTEER = 1000     # Assign this many per volunteer
NUM_VOLUNTEERS = 10                 # How many volunteers
```

Run:
```bash
python scripts/generate_codes.py
```

This prints a table and saves `volunteer_codes.json`.

**Share individual codes only. Never share `volunteer_codes.json`.**

---

## Monitoring Progress

Check collected texts at:
```
https://huggingface.co/datasets/ghananlpcommunity/prestine-twi
```

Dataset is stored as `data.parquet` with columns:
- `id`: Unique identifier (index + volunteer hash)
- `volunteer_hash`: 8-character volunteer identifier
- `source_paragraph`: Original English paragraph
- `twi_text`: Generated Twi text (cleaned)
- `char_count`: Character count of Twi text
- `repetitions_removed`: Number of repeated sentences removed
- `timestamp`: Collection timestamp

Each volunteer has a unique 8-character hash (derived from their code). Commits show:
```
Volunteer a3f8c912: +10 text(s)
```

The dataset is viewable in HuggingFace's dataset viewer with all columns.

---

## Troubleshooting

**Volunteer needs more paragraphs**
Increase `PARAGRAPHS_PER_VOLUNTEER` or `NUM_VOLUNTEERS` and regenerate codes. Existing codes remain valid.

**Push failures**
Check HF token has write access to `ghananlpcommunity/prestine-twi`. Token is base64-encoded in `collector.py` (line 13).

**Volunteer restarts**
They re-run `python collector.py` — already collected texts are skipped automatically.

**Dataset issues**
Input dataset must be at `ghananlpcommunity/twi-english-paragraph-dataset_news` with `train.parquet` containing `ENGLISH` column.
