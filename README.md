# 🏘️ NeighbourGood

**v1.0.0** · A self-hostable web platform that helps communities share resources and coordinate during crises.

## 💡 Vision

Modern neighbourhoods have everything they need — the problem is that resources sit idle in individual households. NeighbourGood makes it easy to share tools, vehicles, equipment, food, and skills within a community, reducing waste and building real connections between neighbours.

But sharing goes beyond convenience. When a crisis hits — a flood, a power outage, a pandemic — the same network that shared a drill last Tuesday becomes a lifeline. NeighbourGood's **dual-state architecture** switches the platform from everyday comfort mode into emergency coordination mode with a single action.

## 🔄 Dual-State Architecture

### 🔵 Blue Sky Mode (Normal Operation)

The default mode focuses on community building and resource sharing:

- **Resource Library** – List and browse items available for borrowing (tools, vehicles, electronics, furniture)
- **Skill Exchange** – Offer and request skills (tutoring, repairs, cooking, languages)
- **Calendar Booking** – Reserve items with date/time slots
- **Gamification** – Earn reputation points for sharing, build trust scores
- **Community Feed** – Updates, requests, offers in a neighbourhood timeline

### 🔴 Red Sky Mode (Crisis Operation)

Activated by an admin or community vote when an emergency occurs:

- **Low-Bandwidth UI** – Text-based, high-contrast, no heavy images
- **Essential Resources Focus** – Food stocks, water filters, generators, medical supplies
- **Emergency Ticketing** – Replace booking with Request / Offer / Emergency Ping
- **Neighbourhood Leaders** – Pre-defined coordinators who can triage and assign
- **Offline-First** – PWA with local caching, mesh networking preparation

## 🛠️ Tech Stack

| Layer      | Technology                     | Why                                              |
| ---------- | ------------------------------ | ------------------------------------------------ |
| Backend    | Python + FastAPI               | Lightweight, async, easy to extend with AI later  |
| Frontend   | SvelteKit                      | Fast, small bundles, good PWA/offline support     |
| Database   | PostgreSQL (prod) / SQLite (dev) | PostgreSQL in Docker for production, SQLite for quick local dev |
| Deployment | Docker Compose                 | Single `docker-compose up` to run everything      |

## 🚀 Quick Start

### With Docker (recommended)

```bash
git clone https://github.com/alcoolio/neighbourgood.git
cd neighbourgood
cp .env.example .env

# Generate a secret key (required — the app won't start without it)
echo "NG_SECRET_KEY=$(openssl rand -hex 32)" >> .env

docker compose up --build
```

- Frontend: http://localhost:3800
- Backend API: http://localhost:8300
- API docs: http://localhost:8300/docs

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For local dev, enable debug mode (allows default secret key + SQLite)
NG_DEBUG=true uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
neighbourgood/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config.py           # Settings and environment config
│   │   ├── database.py         # SQLAlchemy database setup
│   │   ├── dependencies.py     # Auth dependencies (get_current_user)
│   │   ├── models/             # SQLAlchemy models (User, Resource, Booking, Message, Community)
│   │   ├── routers/            # API route handlers
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic (auth, JWT, email notifications)
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── routes/             # SvelteKit pages
│   │   ├── lib/                # Shared components, API client, stores
│   │   └── app.css             # Global styles (Blue/Red Sky themes)
│   ├── static/                 # Static assets and PWA manifest
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml          # One-command deployment
├── .env.example                # Configuration template
├── CHANGELOG.md
└── README.md
```

## 📡 API

See [API_ENDPOINTS.md](API_ENDPOINTS.md) for the full endpoint reference. Interactive docs at `/docs` when the backend is running.

## 🗺️ Roadmap

### Phase 1 — Foundation (MVP) ✅

- [x] Project scaffold (FastAPI + SvelteKit + Docker)
- [x] `/status` endpoint with dual-mode indicator
- [x] Blue Sky / Red Sky CSS theme system
- [x] User registration and authentication (JWT)
- [x] User profiles with neighbourhood assignment
- [x] Basic resource listing (CRUD for items)
- [x] Resource detail page
- [x] SQLite database with Alembic migrations

### Phase 2 — Core Sharing ✅

- [x] Resource categories (tools, vehicles, electronics, furniture, food, clothing)
- [x] Image upload for resources
- [x] Search and filter resources
- [x] Calendar-based booking system
- [x] Request/approve flow for borrowing
- [x] User messaging (in-app)
- [x] Email notifications

### Phase 3 — Community & Trust ✅

- [x] Skill exchange listings (offer/request with 10 categories)
- [x] Reputation/trust score system (computed from activity, 5 levels)
- [x] Community feed / activity timeline (auto-generated from events)
- [x] Neighbourhood groups (Hybrid: PLZ-based with custom names)
- [x] Community merge function with auto-suggestions
- [x] Onboarding flow (search/join/create community)
- [x] Community-scoped resources (soft scoping with community_id)
- [x] Instance identity and `/instance/info` endpoint (federation prep)
- [x] PostgreSQL production default (Docker Compose)
- [x] Invite system for new members (code-based, with expiry/max uses)
- [x] Rating and review system for transactions (1-5 stars, per-booking)

### Phase 3.5 — Federation Preparation ✅

- [x] Instance metadata with admin accountability (name, region, contact)
- [x] `/instance/info` public endpoint for directory crawling
- [x] Instance directory (discover other NeighbourGood instances)
- [x] Cross-instance Red Sky alerts
- [x] User data export (portable backup)
- [x] Instance migration tooling

### Phase 4 — Red Sky Mode 🚨

- [x] Admin toggle for crisis mode (per-community)
- [x] Community vote mechanism for mode activation (60% threshold)
- [x] Emergency ticketing system (Request / Offer / Emergency Ping)
- [x] Neighbourhood leader roles and assignment
- [x] Explore page with community map for unregistered users
- [x] Low-bandwidth UI variant (text-only, image-free mode)
- [x] Essential resource inventory tracking (quantity-based stock management)
- [x] Priority-based ticket triage (triage dashboard for leaders/admins)

#### Security Phase 4a — Hardening ✅

- [x] Password strength validation (min 8 chars, uppercase + lowercase + digit)
- [x] Email format validation (EmailStr)
- [x] Security response headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS)
- [x] Secret key validation (reject default key in production, require 32+ chars)
- [x] File upload hardening (magic byte validation, extension sanitisation)
- [x] Input length limits on all user-facing schemas

#### Security Phase 4b — Access Control

- [ ] Rate limiting on auth endpoints (login, register)
- [ ] Account lockout after repeated failed login attempts
- [ ] CSRF protection for state-changing operations
- [ ] Session invalidation on password change
- [ ] Audit logging for admin actions

#### Security Phase 4c — Data Protection

- [ ] Field-level encryption for sensitive data (email, messages)
- [ ] Automated database backups with encryption at rest
- [ ] PII anonymisation for deleted accounts
- [ ] Content Security Policy tuning per route
- [ ] Dependency vulnerability scanning (CI integration)

### Phase 5 — Offline & Resilience

- [x] Full PWA with service worker caching ✅ (v0.9.9)
- [ ] Offline item browsing and request queuing
- [ ] Background sync when connectivity returns
- [ ] Data export and backup tools

#### Security Phase 5a — Infrastructure

- [ ] TLS certificate automation (Let's Encrypt)
- [ ] Container image scanning and hardening
- [ ] Network segmentation (backend ↔ database)
- [ ] Secrets management (Vault / sealed secrets)
- [ ] Incident response runbook

### Phase 6 — Advanced Features

- [ ] AI-powered resource matching and recommendations
- [ ] Mesh networking preparation (bitchat API integration)
- [ ] Decentralized data sync between instances
- [ ] Multi-language support (i18n)
- [ ] Admin dashboard with analytics
- [x] Outbound webhook system with HMAC-SHA256 signing (generic integrations)
- [x] Telegram bot integration (personal notifications, community group alerts, bot commands)
- [ ] Signal integration
- [ ] Matrix integration

## 🤖 Telegram Bot Setup

NeighbourGood can send notifications to personal Telegram accounts and community group chats, and respond to bot commands.

### 1. Create a bot

Open a conversation with [@BotFather](https://t.me/BotFather) and run:

```
/newbot
```

Follow the prompts to choose a name and username. Copy the **API token** you receive.

### 2. Configure the environment

Add the following to your `.env` file (or Docker environment):

```env
NG_TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NG_TELEGRAM_BOT_NAME=your_bot_username   # without the @ prefix
NG_TELEGRAM_WEBHOOK_SECRET=some-random-string-at-least-32-chars
```

### 3. Register the webhook with Telegram

After the backend is running, call Telegram's `setWebhook` endpoint once:

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://<your-domain>/telegram/webhook" \
  -d "secret_token=<NG_TELEGRAM_WEBHOOK_SECRET>"
```

Replace `<your-domain>` with the public URL of your NeighbourGood instance (must be HTTPS). For local development you can use a tunnel such as [ngrok](https://ngrok.com/).

### 4. Link accounts

**Personal notifications** — users go to **Settings → Telegram** and click the link button. This opens a deep link (`t.me/your_bot?start=TOKEN`) that lets the bot identify them and store their chat ID.

**Community group chat** — a community admin:
1. Adds the bot to the Telegram group.
2. Goes to **Settings → Telegram** (community section) and copies the generated link token.
3. Types `/link <token>` in the group. The bot then recognises the group and will send community-wide announcements there.

### 5. Bot commands

Once a community group is linked, members can query the community directory:

| Command | Description |
|---------|-------------|
| `/profile <name>` | Show a neighbour's reputation score and community role |
| `/lending <name>` | List resources a neighbour currently has available to borrow |
| `/skills <name>` | List skills a neighbour is offering or requesting |

### Events sent to Telegram

| Event | Personal | Community group |
|-------|----------|----------------|
| New message received | ✅ | — |
| Booking created | ✅ (resource owner) | — |
| Booking status changed | ✅ (borrower) | — |
| New resource shared | — | ✅ (all modes) |
| New skill posted | — | ✅ (all modes) |
| Member joined | — | ✅ (all modes) |
| Emergency ticket created | ✅ | ✅ (Red Sky only) |
| Crisis mode changed | ✅ (all members) | — |

### Webhooks (generic)

Any external service can receive the same events via **Settings → Webhooks**. POST requests are signed with `X-Signature: sha256=<hmac>` using the secret you provide. Supported events mirror the table above.

## 🤝 Contributing

This project is in its early stages. Contributions, ideas, and feedback are welcome.

## 📄 License

See [LICENSE](LICENSE) for details.
