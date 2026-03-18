# FounderGraph AI Workflows

Modular, parallelizable OpenClaw workflows: morning digests, marketing assistants, research monitors, and more.

```bash
# Coming soon: pip install fgai-workflows
```

## Modules

- `workflows.digest` — Morning digest: news + calendar + custom summaries
- `workflows.marketing` — Content ideation, competitor tracking
- `workflows.research` — Deep-dive reports with citations

## Development

```bash
git clone https://github.com/foundergraphai/workflows.git
cd workflows
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## License

MIT