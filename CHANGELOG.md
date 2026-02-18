# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.6.0] - 2026-02-18

### Added

- **Instance identity** – Configurable instance metadata (name, region, admin contact) for federation readiness
- **`/instance/info` endpoint** – Public metadata endpoint for federation directory crawling
- **Community-scoped resources** – Resources can belong to a community via `community_id` (nullable for personal items)
- **Community resource filter** – `GET /resources?community_id=` filters resources by community
- **Community resources view** – Community detail page shows resources shared within that community
- **Community selector on create** – Resource creation form lets users assign resources to their communities
- **PostgreSQL production default** – Docker Compose now runs PostgreSQL 16; SQLite remains for local dev
- **101 tests** – Added 8 tests for instance info, community-scoped resource CRUD and filtering

### Changed

- Docker Compose uses PostgreSQL with dedicated `pg-data` volume instead of SQLite
- `.env.example` expanded with instance identity and admin contact fields
- `psycopg2-binary` added to backend requirements
- Alembic `env.py` now imports all models for complete migration generation

## [0.5.0] - 2026-02-18

### Added

- **Community system** – PLZ-based neighbourhood groups with custom names
- **Community CRUD** – Create, search, join, leave, update communities
- **Community merge** – Merge smaller communities into larger ones (admin only)
- **Merge suggestions** – Auto-suggest merge candidates by same postal code or city
- **Onboarding flow** – Post-registration search for community by city/name/PLZ, join or create
- **Community frontend** – My Communities list, community detail with members, merge UI for admins
- **Alembic migration** – Communities and community_members tables
- **93 tests** – Added 24 tests for community CRUD, membership, merge, suggestions, and search

### Changed

- **Shared frontend types** – Centralized TypeScript interfaces in `$lib/types.ts`, replacing duplicated local definitions
- **CSS utility classes** – Global alert, tag, badge, empty-state, and loading classes in `app.css`
- **Hardcoded colors removed** – All frontend pages now use CSS variables for dark mode compatibility
- **N+1 query fix** – Bulk-fetch conversation partners in messages endpoint
- **FK indexes** – Added `index=True` to all foreign key columns across models for query performance
- **Configurable frontend URL** – Notification emails use `frontend_url` setting instead of hardcoded localhost
- **Removed redundant schema** – Eliminated `CommunitySearch` (duplicate of `CommunityList`)
- Registration now redirects to `/onboarding` instead of `/resources`

## [0.4.0] - 2026-02-17

### Added

- **In-app messaging** – Direct messages between users with conversation threads
- **Conversation list** – Overview of all conversations with last message preview and unread badges
- **Unread tracking** – Per-message and per-conversation read status, unread count endpoint
- **Booking-linked messages** – Attach messages to specific booking requests for context
- **Mark as read** – Mark individual messages or entire conversations as read
- **Email notifications** – SMTP-based notifications for new messages, booking requests, and status changes
- **Graceful fallback** – Logs notifications to console when SMTP is not configured
- **Messages frontend** – Conversation list with chat-style message thread and compose input
- **Nav update** – Messages link in navigation bar for logged-in users
- **Alembic migration** – Messages table with sender/recipient/booking foreign keys
- **69 tests** – Added 18 tests for messaging, conversations, read status, and notification service

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
