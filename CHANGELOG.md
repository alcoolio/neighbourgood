# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-02-17

### Added

- **User authentication** – Register and login with email/password, JWT-based sessions
- **User profiles** – View and update display name, neighbourhood assignment
- **Resource CRUD** – Create, read, update, and delete shared resources
- **Resource categories** – tool, vehicle, electronics, furniture, food, clothing, skill, other
- **Category filtering** – Filter resource listings by category
- **Resource detail page** – View full resource info with owner details
- **Owner actions** – Toggle availability, delete own resources
- **Frontend auth flow** – Registration, login, and logout with persistent JWT storage
- **Frontend resource pages** – Resource listing with create form, detail view with owner controls
- **Navigation bar** – Global nav with auth-aware links
- **API client** – Reusable fetch wrapper with auth header injection
- **Alembic migrations** – Database schema versioning for users and resources tables
- **Test suite** – 15 tests covering status, auth, users, and resource endpoints

## [0.1.0] - 2026-02-17

### Added

- Initial project scaffold with FastAPI backend and SvelteKit frontend
- `/status` health-check endpoint with dual-mode indicator (blue/red)
- Blue Sky / Red Sky CSS theme system using CSS custom properties
- SQLAlchemy database setup with SQLite default and PostgreSQL option
- Pydantic-settings configuration with `NG_` prefixed environment variables
- Docker Compose single-command deployment
- PWA manifest for offline-first preparation
- README with project vision, architecture documentation, and 6-phase roadmap
