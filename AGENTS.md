# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: Flask API, route blueprints (`backend/routes/`), service layer (`backend/services/`), provider adapters (`backend/generators/`), and prompt templates (`backend/prompts/`).
- `frontend/`: Vue 3 + TypeScript app (Vite). Main app code is in `frontend/src/` (`views/`, `components/`, `stores/`, `api/`).
- `tests/`: Python test scaffolding and shared fixtures (`tests/conftest.py`). Add backend tests here as `test_*.py`.
- `docker/`, `Dockerfile`, `docker-compose.yml`: container deployment assets.
- Runtime/config data: `history/`, `data/`, `text_providers.yaml`, `image_providers.yaml`.

## Build, Test, and Development Commands
- Preferred startup on Windows (backend + frontend together): `start.bat`
- Install backend deps: `uv sync`
- Run backend locally: `uv run python -m backend.app` (serves API on `http://localhost:12398`)
- Install frontend deps: `cd frontend && pnpm install`
- Run frontend dev server: `cd frontend && pnpm dev` (default `http://localhost:5173`)
- Build frontend: `cd frontend && pnpm build`
- Preview frontend build: `cd frontend && pnpm preview`

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes, keep route handlers thin and move logic into `backend/services/`.
- TypeScript/Vue: `PascalCase` for component files (for example `ProviderModal.vue`), composables as `useXxx.ts`, Pinia stores in `frontend/src/stores/`.
- Prefer small, focused modules over large mixed-responsibility files.
- No formatter/linter config is currently committed; keep style consistent with surrounding files.

## Testing Guidelines
- Framework: `pytest` (fixtures already defined in `tests/conftest.py`).
- Add tests as `tests/test_<feature>.py`; name test functions `test_<behavior>()`.
- Run tests with `uv run pytest tests`.
- Prioritize coverage for routes, service logic, and config edge cases (missing provider keys, invalid payloads).

## Commit & Pull Request Guidelines
- Follow existing history style: conventional prefixes such as `feat:`, `fix:`, `refactor:` plus a concise summary.
- Keep each commit scoped to one change area (backend API, frontend UI, config, docs).
- PRs should include: purpose, key changes, test evidence (commands/output), linked issue, and UI screenshots for frontend changes.
- If configuration behavior changes, document required updates to `*.yaml.example` files in the PR.
