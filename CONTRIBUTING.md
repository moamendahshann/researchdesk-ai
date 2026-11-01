# Contributing

Use Python 3.11 or 3.12 in a virtual environment. Install `requirements-dev.txt`, run `python -m pytest -q` and `python -m tests.evaluate`, then start the workspace with `python -m app`.

Use synthetic or openly shareable PDFs in tests and screenshots. Do not commit personal documents, the SQLite workspace, provider keys or API responses containing private data.

Keep lexical retrieval and optional model generation distinct. Report evaluation scope, expected source pages and limitations when changing ranking. Citation-ID checks do not establish that an answer is factually supported.

Submit focused pull requests with the problem, implementation and validation. This is a local single-user application; public multi-user hosting requires additional design and access controls.

No open-source license has been selected; see the repository's README before reusing code.
