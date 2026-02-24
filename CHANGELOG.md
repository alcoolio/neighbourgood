# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.5] - 2026-02-24

### Added

- **Low-bandwidth mode** – Text-only, image-free UI for reduced data usage
  - Hidden by default in Blue Sky; auto-enabled in Red Sky mode
  - Triage dashboard for managing emergency tickets (Red Sky only)
  - Inventory tracking system for essential resource quantities
- **CLAUDE.md codebase guide** – Comprehensive reference for AI assistants
  - Model usage policy and token efficiency guidelines
  - Project overview, tech stack, and repository structure
  - Development workflows, testing patterns, and common task recipes
  - Security state tracking with pending items and implementation status
- **Community-filtered resources and skills** – Search/filter now respects joined communities
  - API endpoints filter results to only show resources/skills from communities the user has joined
  - Prevents information leakage of resources in other communities
- **Eager-loading for community relationships** – N+1 query fix
  - Communities serialize with members, resources, and skills without extra round-trips
  - Improved API response time and database efficiency
- **Enhanced API error handling** – Better Pydantic validation error messages
  - Detailed field-level error information for easier client-side debugging
  - Consistent error response format across all endpoints

### Fixed

- **Community 500 error** – Fixed serialization issues when accessing community endpoints
- **Community-scoped resource/skill filtering** – Correct community membership checks on queries
- **Other bug fixes** – Stability improvements across multiple endpoints

### Changed

- Backend version bumped to 0.9.5
- **Red Sky Mode improvements** – Low-bandwidth mode now defaults to on when crisis mode is active
- Low-bandwidth and triage features are production-ready and integrated into crisis workflow

## [0.9.0] - 2026-02-19

### Added

- **Per-community crisis mode** – Communities can switch between Blue Sky (normal) and Red Sky (crisis) modes
- **Admin crisis toggle** – Community admins can force-toggle crisis mode via `POST /communities/{id}/crisis/toggle`
- **Community vote mechanism** – Members can vote to activate/deactivate crisis mode; auto-switches at 60% threshold
- **Crisis mode status** – `GET /communities/{id}/crisis/status` shows current mode, vote counts, and threshold
- **Emergency ticketing system** – Create request, offer, and emergency ping tickets within communities
  - Emergency pings restricted to Red Sky mode only
  - Ticket CRUD with type/status/urgency filters
  - Authors, leaders, and admins can update tickets
- **Neighbourhood leader roles** – Admins can promote members to "leader" role, leaders can manage tickets
  - `POST /communities/{id}/leaders/{user_id}` to promote
  - `DELETE /communities/{id}/leaders/{user_id}` to demote
  - `GET /communities/{id}/leaders` to list leaders
- **Explore page (landing for guests)** – Map-based community discovery using Leaflet/OpenStreetMap
  - Browser geolocation to center map on user's position
  - Community markers with member count badges
  - Community list cards with crisis mode indicators
  - Register CTA for unregistered users
- **Public map endpoint** – `GET /communities/map` returns lightweight community data (no auth required)
- **Community coordinates** – Optional latitude/longitude fields on communities for map placement
- **Guest-friendly navigation** – Logged-out users see "Explore" instead of Resources/Skills
- **Crisis mode UI** – Community detail page shows crisis status, vote buttons, emergency tickets, and leader management
- **198 tests** – Added 32 tests for crisis toggle, voting, tickets, leaders, and map endpoint

### Changed

- Community model extended with `mode` (blue/red), `latitude`, and `longitude` fields
- CommunityMember role now supports "member", "leader", and "admin"
- CommunityOut schema includes `mode`, `latitude`, `longitude` fields
- Navigation hides Resources/Skills for logged-out users, shows Explore link instead
- Activity event types expanded: `crisis_mode_changed`, `ticket_created`, `leader_promoted`, `leader_demoted`
- Backend version bumped to 0.9.0

## [0.8.0] - 2026-02-19

### Added

- **Mobile navigation** – Hamburger menu with slide-down nav for screens ≤768px, overlay backdrop, animated open/close
- **Community-scoped messaging** – Messages restricted to users who share at least one community (403 if no shared community)
- **New Message button** – Contact picker modal on messages page; lists community members with search filter
- **Messageable contacts endpoint** – `GET /messages/contacts` returns all users sharing a community with the current user
- **Security Phase 1 (4a)** – First security hardening pass:
  - Password strength validation (min 8 chars, uppercase + lowercase + digit required)
  - Email format validation via `EmailStr` on register and login
  - Security response headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS, CSP)
  - Secret key validation (rejects default key in production, requires 32+ chars)
  - File upload hardening (magic byte validation, extension sanitisation, allowed-list enforcement)
  - Input length limits on all user-facing schemas (titles, descriptions, messages, names)
- **Security roadmap** – Three security phases mapped to main phases 4 and 5 in README
- **166 tests** – Added 3 tests for community-scoped messaging and messageable contacts

### Changed

- Navigation header is fully responsive with hamburger menu on mobile
- Messages page header uses flexbox layout with "New Message" action button
- `pydantic[email]` added to backend requirements for `EmailStr` support
- Backend version bumped to 0.8.0

## [0.7.0] - 2026-02-18

### Added

- **Skill exchange listings** – Offer or request skills with 10 categories (tutoring, repairs, cooking, languages, music, gardening, tech, crafts, fitness, other)
- **Full skills CRUD** – `/skills` endpoints with search, category/type filters, and community scoping
- **Skills frontend page** – Browse, search, filter, and create skill listings with offer/request badges
- **Reputation/trust score system** – Computed score from sharing activity: resources shared (5pts), lending completed (10pts), borrowing completed (3pts), skills offered (5pts), skills requested (2pts)
- **5 reputation levels** – Newcomer → Neighbour → Helper → Trusted → Pillar
- **Reputation endpoints** – `GET /users/me/reputation` (auth), `GET /users/{id}/reputation` (public)
- **Community activity feed** – Auto-generated timeline from resource sharing, bookings, skills, and member joins
- **Activity endpoints** – `GET /activity` (public, filter by community), `GET /activity/my` (auth)
- **Invite system** – Generate URL-safe invite codes for communities with optional max_uses and expiry
- **Invite CRUD** – Create, list, redeem, and revoke invite codes
- **Rating and review system** – 1-5 star reviews on completed bookings for both borrower and lender
- **Review summary** – Average rating and total review count per user
- **163 tests** – Added 70 tests for skills, reputation, activity, invites, and reviews

### Changed

- Skills nav link added to main navigation (visible to all users)
- Activity events auto-recorded when resources are shared, bookings created/completed, skills posted, and members join communities
- Homepage: 6-box feature grid, GitHub social preview image, bright mode default
- Backend version bumped to 0.7.0

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
