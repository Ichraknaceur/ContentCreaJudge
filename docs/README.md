# ContentCreaJudge

[![Python](https://img.shields.io/badge/Python-FFD43B?logo=python)](https://www.python.org/)
![License](https://img.shields.io/badge/GPL--3.0-red?logo=gnu)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-E6F0FF?logo=githubactions)](https://github.com/features/actions)
[![Pytest](https://img.shields.io/badge/pytest-E6F7FF?logo=pytest)](https://docs.pytest.org/)
[![EditorConfig](https://img.shields.io/badge/EditorConfig-333333?logo=editorconfig)](https://editorconfig.org/)
[![uv](https://img.shields.io/badge/uv-261230?logo=astral)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/Ruff-3A3A3A?logo=ruff)](https://docs.astral.sh/ruff/)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![Pre-commit](https://img.shields.io/badge/pre--commit-40332E?logo=pre-commit)](https://pre-commit.com/)
[![Makefile](https://img.shields.io/badge/Makefile-427819?logo=gnu)](https://www.gnu.org/software/make/manual/make.html)
[![MkDocs](https://img.shields.io/badge/MkDocs-526CFE?logo=markdown)](https://www.mkdocs.org/)

## Overview

AI-assisted engine for evaluating and improving editorial content quality and compliance.

Current V1 foundation already includes:

- FastAPI backend bootstrap
- `GET /`
- `GET /health`
- `POST /api/v1/evaluations`
- Streamlit UI client aligned with the ContentCrea visual theme

## Setup and installation

### Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installation

```sh
make init
```

## Usage

### Run the backend API

```sh
make run
```

The API is exposed locally at:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/evaluations`

### Run the Streamlit UI

```sh
make run-ui
```

The UI is exposed locally at:

- `http://127.0.0.1:8501`

### Current UI Scope

The Streamlit UI currently provides:

- backend connection status
- API overview
- evaluation payload form
- response console
- delivery view for client demos

## Development

### Architecture and Internal Guides

The project documentation now includes dedicated references for system design and
internal development practices:

- [Cadrage Équipe](CADRAGE_EQUIPE.md)
- [Architecture](ARCHITECTURE.md)
- [Configuration Des Règles](RULES_CONFIGURATION.md)
- [API Contract](API_CONTRACT.md)
- [Developer Guide](DEVELOPER_GUIDE.md)

### Code Formatting and Linting

Useful commands:

- `make lint`
- `make typecheck`
- `make test`
- `make docs`

### Environment Variables

| Variable | Description | Required | Default Value | Possible Values |
|----------|-------------|----------|---------------|-----------------|
| `CONTENTCREAJUDGE_API_URL` | Backend base URL used by the Streamlit UI | No | `http://127.0.0.1:8000` | Any valid `http` or `https` URL |

### Architecture

The V1 service architecture follows a modular evaluation pipeline:

```text
Request -> Validation -> Rule Resolution -> Preprocessing -> Judges
-> Aggregation -> Response
```

The current implementation also includes a presentation layer for demos:

```text
Streamlit UI -> FastAPI API -> Evaluation endpoint scaffold
```

For the full design, module boundaries, and internal guidelines, see the
architecture and developer guide pages linked above.

## Contributing

We welcome contributions to this project! Please see
the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to
contribute, including:

- How to set up your development environment
- Coding standards and style guidelines
- Pull request process
- Testing requirements

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) -
see the LICENSE file for details.

GPL-3.0 is a strong copyleft license that requires anyone who distributes your
code or a derivative work to make the source available under the same terms.
