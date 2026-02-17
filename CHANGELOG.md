# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-02-17

### Added

- **Calendar-based booking system** – Request to borrow resources with date ranges, conflict detection
- **Booking status workflow** – Pending → Approved/Rejected (owner), Cancelled (borrower), Completed
- **Resource search** – Full-text search across titles and descriptions (case-insensitive)
- **Image upload** – Upload images for resources with type/size validation (JPEG, PNG, WebP, GIF)
- **Category metadata** – Categories endpoint with labels and icon names
- **Availability filter** – Filter resources by availability status
- **Bookings management page** – Frontend page with role/status filters, approve/reject/cancel/complete actions
- **Resource calendar view** – API endpoint for month-based booking calendar per resource
- **Booking form** – Request-to-borrow form on resource detail page with date range and message
- **Alembic migration** – Bookings table and image_path column for resources
- **51 tests** – Added 34 tests for search, image upload, categories, bookings CRUD, status transitions, calendar

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
- **Test suite** – 17 tests covering status, auth, users, and resource endpoints

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
