# NeighbourGood

A self-hostable web platform that helps communities share resources and coordinate during crises.

## Vision

Modern neighbourhoods have everything they need — the problem is that resources sit idle in individual households. NeighbourGood makes it easy to share tools, vehicles, equipment, food, and skills within a community, reducing waste and building real connections between neighbours.

But sharing goes beyond convenience. When a crisis hits — a flood, a power outage, a pandemic — the same network that shared a drill last Tuesday becomes a lifeline. NeighbourGood's **dual-state architecture** switches the platform from everyday comfort mode into emergency coordination mode with a single action.

## Dual-State Architecture

### Blue Sky Mode (Normal Operation)

The default mode focuses on community building and resource sharing:

- **Resource Library** – List and browse items available for borrowing (tools, vehicles, electronics, furniture)
- **Skill Exchange** – Offer and request skills (tutoring, repairs, cooking, languages)
- **Calendar Booking** – Reserve items with date/time slots
- **Gamification** – Earn reputation points for sharing, build trust scores
- **Community Feed** – Updates, requests, offers in a neighbourhood timeline

### Red Sky Mode (Crisis Operation)

Activated by an admin or community vote when an emergency occurs:

- **Low-Bandwidth UI** – Text-based, high-contrast, no heavy images
- **Essential Resources Focus** – Food stocks, water filters, generators, medical supplies
- **Emergency Ticketing** – Replace booking with Request / Offer / Emergency Ping
- **Neighbourhood Leaders** – Pre-defined coordinators who can triage and assign
- **Offline-First** – PWA with local caching, mesh networking preparation

## Tech Stack

| Layer      | Technology                     | Why                                              |
| ---------- | ------------------------------ | ------------------------------------------------ |
| Backend    | Python + FastAPI               | Lightweight, async, easy to extend with AI later  |
| Frontend   | SvelteKit                      | Fast, small bundles, good PWA/offline support     |
| Database   | SQLite (default) / PostgreSQL  | Zero-config default, scale up when needed         |
| Deployment | Docker Compose                 | Single `docker-compose up` to run everything      |

## Quick Start

### With Docker (recommended)

```bash
git clone https://github.com/alcoolio/neighbourgood.git
cd neighbourgood
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
neighbourgood/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── config.py         # Settings and environment config
│   │   ├── database.py       # SQLAlchemy database setup
│   │   ├── models/           # Database models
│   │   ├── routers/          # API route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic
│   ├── tests/                # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── routes/           # SvelteKit pages
│   │   ├── lib/              # Shared components and utilities
│   │   └── app.css           # Global styles (Blue/Red Sky themes)
│   ├── static/               # Static assets and PWA manifest
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml        # One-command deployment
├── .env.example              # Configuration template
└── README.md
```

## API

| Endpoint  | Method | Description                              |
| --------- | ------ | ---------------------------------------- |
| `/status` | GET    | Health check, version, current mode      |

## Roadmap

### Phase 1 — Foundation (MVP)

- [x] Project scaffold (FastAPI + SvelteKit + Docker)
- [x] `/status` endpoint with dual-mode indicator
- [x] Blue Sky / Red Sky CSS theme system
- [ ] User registration and authentication (email + password)
- [ ] User profiles with neighbourhood assignment
- [ ] Basic resource listing (CRUD for items)
- [ ] Simple item detail page
- [ ] SQLite database with Alembic migrations

### Phase 2 — Core Sharing

- [ ] Resource categories (tools, vehicles, electronics, furniture, food, clothing)
- [ ] Image upload for resources
- [ ] Search and filter resources
- [ ] Calendar-based booking system
- [ ] Request/approve flow for borrowing
- [ ] User messaging (in-app)
- [ ] Email notifications

### Phase 3 — Community & Trust

- [ ] Skill exchange listings
- [ ] Reputation/trust score system
- [ ] Community feed / activity timeline
- [ ] Neighbourhood groups and boundaries
- [ ] Invite system for new members
- [ ] Rating and review system for transactions

### Phase 4 — Red Sky Mode

- [ ] Admin toggle for crisis mode
- [ ] Community vote mechanism for mode activation
- [ ] Emergency ticketing system (Request / Offer / Emergency Ping)
- [ ] Neighbourhood leader roles and assignment
- [ ] Low-bandwidth UI variant
- [ ] Essential resource inventory tracking
- [ ] Priority-based ticket triage

### Phase 5 — Offline & Resilience

- [ ] Full PWA with service worker caching
- [ ] Offline item browsing and request queuing
- [ ] Background sync when connectivity returns
- [ ] Data export and backup tools
- [ ] Optional PostgreSQL migration path

### Phase 6 — Advanced Features

- [ ] AI-powered resource matching and recommendations
- [ ] Mesh networking preparation (bitchat API integration)
- [ ] Decentralized data sync between instances
- [ ] Multi-language support (i18n)
- [ ] Admin dashboard with analytics
- [ ] Webhook integrations (Telegram, Signal, Matrix)

## Contributing

This project is in its early stages. Contributions, ideas, and feedback are welcome.

## License

See [LICENSE](LICENSE) for details.
