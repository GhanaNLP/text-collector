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

The code generation script now takes the HF token as a command-line argument (not hardcoded).

**Usage:**
```bash
cd scripts
python generate_codes.py <hf_token> [--target-samples N] [--volunteers N]
```

**Examples:**
```bash
# Generate 10,000 texts split across 10 volunteers (1,000 each)
python generate_codes.py hf_TOKEN --target-samples 10000 --volunteers 10

# Generate 5,000 texts split across 5 volunteers (1,000 each)
python generate_codes.py hf_TOKEN --target-samples 5000 --volunteers 5

# Use defaults (10,000 samples, 10 volunteers)
python generate_codes.py hf_TOKEN
```

**Parameters:**
- `hf_token`: HuggingFace token with write access to `ghananlpcommunity/prestine-twi`
- `--target-samples`: Total number of Twi texts to generate (default: 10,000)
- `--volunteers`: Number of volunteers to distribute work across (default: 10)

**How it works:**
- Each prompt paragraph generates 1 Twi text (4-part: monologue, narrative, dialogue, storyful)
- Script assigns unique paragraphs to each volunteer (no overlap)
- Work is split evenly; last volunteer gets any remainder
- Maximum: 257,000 samples (total paragraphs in dataset)

This prints a table and saves `volunteer_codes.json`.

**IMPORTANT SECURITY NOTES:**
- HF token is NOT stored in the script — you provide it each time
- Each volunteer code contains the token embedded (base64-encoded)
- Token should have fine-grained write access ONLY to `ghananlpcommunity/prestine-twi`
- Share individual codes ONLY with trusted volunteers
- Keep `volunteer_codes.json` PRIVATE
- Never commit `volunteer_codes.json` to git

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

**Need more/fewer samples**
Re-run `generate_codes.py` with different `--target-samples` value. Existing codes become invalid (regenerate all).

**Need more/fewer volunteers**
Re-run `generate_codes.py` with different `--volunteers` value.

**Push failures**
- Ensure HF token has write access to `ghananlpcommunity/prestine-twi`
- Use HuggingFace fine-grained token with WRITE permission ONLY to that repo
- Check token hasn't expired (HF tokens can have expiration dates)
- Regenerate codes if token was revoked/changed

**Volunteer restarts**
They re-run `python collector.py` — already collected texts are skipped automatically.

**Token leaked/compromised**
1. Revoke the token immediately in HuggingFace settings
2. Generate a new fine-grained token (write access to prestine-twi only)
3. Re-run `generate_codes.py` with new token
4. Redistribute new codes to ALL volunteers (old codes won't work)

**Change target samples mid-project**
1. Calculate how many samples already collected
2. Generate new codes with `--target-samples` set to REMAINING samples needed
3. Assign different paragraph ranges (start from where old codes ended)
4. Distribute new codes to new volunteers

**Dataset issues**
Input dataset must be at `ghananlpcommunity/twi-english-paragraph-dataset_news` with `train.parquet` containing `ENGLISH` column.
