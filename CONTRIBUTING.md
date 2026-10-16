# Contributing to GO2-PIPER Sim-to-Real

This branch extends LeggedManip Lab for GO2-PIPER. Start with [the team handoff](docs/AGENT_HANDOFF_CN.md) and [project rules](AGENTS.md). Current skill evidence belongs in the five maintained documents under `docs/`; historical package results do not describe the latest candidate.

## Environment and scope

Use the existing remote Isaac environment for training, physics evaluation and recording. Do not install project dependencies into system Python or mix Isaac and MuJoCo environments. The root `requirements.txt` covers MuJoCo tools, not Isaac. The handoff records the observed remote environment and resource transfer requirements.

For a new development environment, first provision compatible Isaac Lab/Isaac Sim separately. From the repository root, its Python can install the extension with `python -m pip install -e source/LeggedManip_Lab`. This only registers the extension; it does not fetch the external latest candidates or reproduce their frozen source trees. Do not reinstall or upgrade the shared reference environment as part of routine development.

## Development workflow

1. Check branch, local changes, candidate hashes and active remote processes. Preserve existing changes and frozen evidence.
2. Use a separate output directory for every experiment. Record source revision and overrides, asset/control hashes, full command, seed, environment, physical parameters and checkpoint identity.
3. Run checks relevant to the change. Code uses the Ruff configuration in `pyproject.toml` (120 columns, Google-style docstrings, English comments). If using pre-commit, install/run it in an isolated development environment; hooks may modify files, so review the diff.
4. Preserve observation/action order, history, PD, delay and contact/safety gates. Follow the project plan for physical acceptance; a passing static check is not an accepted skill.
5. For documentation, check relative links and anchors, distinguish historical results from new verification, and check commands against the matching candidate. Update a package's `SHA256SUMS` only for intentionally changed files; never refresh it to hide unexpected drift.
6. Commit a focused change and push to the agreed branch. Describe behavior, evidence and remaining limitations; do not commit credentials, environments, logs, large new artifacts or unverified candidates.

Current project work is on `feature/go2-piper-sim2real`. New work must respect the active scope in the handoff; PUSH and CLIMB MuJoCo transfer diagnostics have resumed, while PUSH Isaac optimization and hardware work remain paused.

## Documentation maintenance

Maintain one source of current status per skill. Keep common environment/transfer guidance in the general handoff, acceptance requirements in the project plan, and calibration in the mounting document. Archive superseded experiment notes with provenance instead of adding new dated status pages. Preserve upstream release history and the [Code of Conduct](CODE_OF_CONDUCT.md).

## Issues and licensing

Report issues with reproduction steps, expected/actual behavior, environment versions, candidate/source hashes and relevant failure evidence. Remove secrets and private connection details before sharing logs. Contributions remain under the repository's Apache 2.0 [license](LICENSE).
