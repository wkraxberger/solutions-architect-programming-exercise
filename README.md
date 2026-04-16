# Smartsheet Account Import

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python setup_workspace.py
```

## Usage

```
python main.py
python main.py --dry-run
python main.py --group-by country,state,city
python main.py --name "Q2 Import" --workspace-id 123
```

## Assumptions

- CSV is trusted input, no validation against malformed data
- Fresh sheet every run, not idempotent
- ARR is always a non negative integer
- Mock data is all US, so I defaulted to country,state hierarchy levels, but more countries work without changes.
- Ruby SDK is archived, so I have chosen python for the maintained SDK

## Questions for the customer

- One-time import or recurring sync?
- Who owns the sheet after import?
- Raw CSV sheet in the same workspace for audit?
- Which geographic dimension matters for reporting?
- Leaves editable or locked?

## With more time

- Retry with backoff on 429/5xx
- Idempotency (update existing sheet instead of creating new)
- Progress bar for large imports
- Tests for the transformer
- Lambda on S3 trigger for production deployment
