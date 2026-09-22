# People Generator

Generate a pool of fake people for testing purposes: names, emails, phones, and
US-style addresses, output as CSV or JSONL. An optional debt-settlement mode adds
credit fields for direct-mail / lead-list style test data.

Every record is entirely fabricated. Names, addresses, phones, and emails are
random and not intended to match any real person. Emails use reserved
`example.*` domains and phone numbers are not guaranteed dialable.

## Requirements

- Python 3.6+
- No external dependencies (standard library only)

## Usage

### Interactive

Run with no arguments in a terminal and it prompts for each option, with defaults
offered inline (press Enter to accept):

```bash
python3 people_generator.py
```

### From a script (non-interactive)

Any flag switches it to non-interactive mode. Piped or non-terminal runs with no
arguments fall back to defaults and never block waiting on input, so it is safe
in cron and CI.

```bash
# 10,000 people to people.csv (the defaults)
python3 people_generator.py --count 10000

# JSONL to stdout
python3 people_generator.py -n 500 -f jsonl -o -

# Direct-mail style list with credit fields and a custom debt range
python3 people_generator.py -n 25000 --debt-settlement --debt-floor 10000 --debt-ceiling 500000 -o leads.csv
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `-n`, `--count N` | `10000` | Number of people to generate |
| `-o`, `--output FILE` | `people.csv` | Output file, or `-` for stdout |
| `-f`, `--format csv\|jsonl` | `csv` | Output format |
| `--seed N` | none | Seed the RNG for repeatable output (see note) |
| `-i`, `--interactive` | off | Force interactive prompts |
| `--debt-settlement` | off | Add credit fields (see below) |
| `--debt-floor N` | `10000` | Minimum `estimated_debt` (with `--debt-settlement`) |
| `--debt-ceiling N` | `500000` | Maximum `estimated_debt` (with `--debt-settlement`) |

## Output fields

Base (always):

```
first_name, last_name, email, phone, address, city, state, zip
```

With `--debt-settlement`, three more are appended:

```
estimated_debt   # random integer between --debt-floor and --debt-ceiling
credit_score     # 300–850
num_creditors    # 1–12
```

`city` and `state` are drawn independently, so they will not always form a real
city/state pair. That is fine for test data; if you need geographically
consistent pairs, that is a future enhancement.

## Reproducibility

Pass `--seed` to make a run repeatable. Given the same seed, the same code, and
the same Python version, the output is byte-for-byte identical. Across different
Python versions the low-level random stream is stable but the higher-level
helpers (`choice`, `randint`) are not contractually guaranteed, so seed-identical
output is only promised within one Python version. For throwaway test data this
rarely matters; leave `--seed` off for fully random output.
