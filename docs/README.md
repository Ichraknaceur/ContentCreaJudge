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

!!! abstract "Project Snapshot"
    ContentCreaJudge is a rule-based editorial evaluation engine with a FastAPI
    backend and a Streamlit demo UI. The current foundation is designed to let
    the team implement mini-judges independently while keeping one stable API
    contract.

## Why This Project Exists

AI-assisted engine for evaluating and improving editorial content quality and compliance.

Current V1 foundation already includes:

- FastAPI backend bootstrap
- `GET /`
- `GET /health`
- `POST /api/v1/evaluations`
- Streamlit UI client aligned with the ContentCrea visual theme

## At A Glance

<div class="grid cards" markdown>

-   __Backend__
    ---
    FastAPI service exposing health, discovery, evaluations, and judge routes.

-   __UI__
    ---
    Streamlit workspace for demos, manual testing, and isolated judge checks.

-   __Rules__
    ---
    YAML-driven rule definitions kept separate from judge execution logic.

-   __Team Docs__
    ---
    Architecture, cadrage, API contract, and error-handling doctrine in one place.

</div>

## Setup and installation

### Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management

### Installation

```sh
make init
```

## Usage

=== "Backend API"

    ```sh
    make run
    ```

    The API is exposed locally at:

    - `http://127.0.0.1:8000/`
    - `http://127.0.0.1:8000/health`
    - `http://127.0.0.1:8000/api/v1/evaluations`

=== "Streamlit UI"

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

!!! note "Recommended local workflow"
    Start the backend first with `make run`, then start the UI with
    `make run-ui`. The judge playground depends on the API being available.

## Development

### Architecture and Internal Guides

The project documentation now includes dedicated references for system design and
internal development practices:

<div class="grid cards" markdown>

-   __Cadrage Équipe__
    ---
    Team operating principles, layer responsibilities, and collaboration rules.

    [Open the guide](CADRAGE_EQUIPE.md)

-   __Architecture__
    ---
    System boundaries, execution flow, package roles, and backend structure.

    [Open the guide](ARCHITECTURE.md)

-   __Error Handling__
    ---
    Internal doctrine for exceptions, HTTP mapping, and stable error payloads.

    [Open the guide](ERROR_HANDLING.md)

-   __Configuration Des Règles__
    ---
    How YAML rules are structured and how judges consume them.

    [Open the guide](RULES_CONFIGURATION.md)

-   __API Contract__
    ---
    Request and response shapes that clients are expected to rely on.

    [Open the guide](API_CONTRACT.md)

-   __Developer Guide__
    ---
    Practical implementation rules for contributors extending the service.

    [Open the guide](DEVELOPER_GUIDE.md)

</div>

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

## Reading Paths

=== "I want to understand the system"

    1. Read [Architecture](ARCHITECTURE.md)
    2. Read [API Contract](API_CONTRACT.md)
    3. Read [Error Handling](ERROR_HANDLING.md)

=== "I want to contribute code"

    1. Read [Cadrage Équipe](CADRAGE_EQUIPE.md)
    2. Read [Developer Guide](DEVELOPER_GUIDE.md)
    3. Run `make lint` and `make test`

=== "I want to work on judges"

    1. Read [Configuration Des Règles](RULES_CONFIGURATION.md)
    2. Read [Error Handling](ERROR_HANDLING.md)
    3. Inspect the existing typography flow as the reference pattern

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
