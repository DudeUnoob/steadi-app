# Steadi

![Steadi Logo](./assets/logo.png)

## Smart Inventory Management for Small Businesses

Steadi is an AI-powered inventory management system that helps small businesses automate their inventory operations with enterprise-grade tools at small business prices.

[![Build Status](https://github.com/steadi/steadi-inventory/workflows/CI/badge.svg)](https://github.com/steadi/steadi-inventory/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)

## Features

- 📊 **Real-time Inventory Dashboard** - Lightning-fast inventory overview with essential metrics and performance indicators
- 🔄 **POS Integration** - Sync with Shopify, Square, and Lightspeed POS systems (15-minute auto-sync)
- 📋 **Central SKU Repository** - Fully relational database with complete audit trail of all inventory changes
- 🔍 **Smart Stock Threshold Engine** - Automated inventory monitoring with predictive reorder points
- 🚨 **Actionable Stock Alerts** - Timely notifications when stock needs replenishing
- 📝 **One-Click Purchase Orders** - Generate and send POs to suppliers with a single click
- 📈 **Essential Analytics** - Track turnover rates, top-sellers, and days-of-stock with intuitive visualizations

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Node.js 18+ (for frontend)

### Installation

#### Backend

```bash
# Clone the repository
git clone https://github.com/steadi/steadi-inventory.git
cd steadi-inventory

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload
```

#### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Architecture

Steadi follows a modern cloud-native architecture:

- **Frontend**: React 18 with TanStack Query and Recharts
- **Backend**: FastAPI with SQLModel ORM
- **Database**: PostgreSQL 16 for relational data, Redis for caching
- **Infrastructure**: AWS (Lambda, Fargate, RDS, ElastiCache)
- **CI/CD**: GitHub Actions with Terraform IaC

## API Documentation

Once the server is running, you can access the internal API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Workflow

Internal development follows these principles:

1. Branch from main (`git checkout -b feature/amazing-feature`)
2. Commit changes with descriptive messages
3. Submit for code review via pull request
4. Merge after approval and CI checks pass

## MoSCoW Prioritization

Our development follows the MoSCoW prioritization framework:

- **Must Have**: Core inventory functionality (dashboard, repository, threshold engine)
- **Should Have**: Integration capabilities (POS connectors, alerts, PO generation)
- **Could Have**: Workflow enhancements (reorder tracking, analytics)
- **Won't Have** (yet): Advanced features planned for future releases

## License

Steadi is proprietary software. All rights reserved.

##Committing
Commit Message Structure
<type>(<scope>): <short summary>

<body>

<footer>

##Types
- feat: A new feature
- fix: A bug fix
- docs: Documentation changes only
- style: Changes that don't affect code functionality (formatting, etc.)
- refactor: Code changes that neither fix bugs nor add features
- test: Adding or modifying tests
- chore: Changes to build process, dependencies, etc.
- perf: Performance improvements

##Scope (Optional)
Indicates what part of the codebase was modified:
- inventory
- auth
- po (purchase orders)
- connector
- api
- db
- ui

##Examples
feat(inventory): implement stock threshold engine

Add automatic calculation of reorder points based on safety stock
and average daily sales. Includes rate-limited alerts for low stock.

Closes #42
________________________________________________________________________________________________
fix(api): correct response format for inventory endpoint

Change API response to match PRD specification by adding badge and
color fields to inventory items.
________________________________________________________________________________________________

refactor(connector): simplify Shopify GraphQL client

Reduce complexity of GraphQL query builder and improve error handling
for rate-limited API responses.
________________________________________________________________________________________________
test(threshold): add unit tests for reorder calculations

Ensure correct behavior with edge cases like zero sales or
custom safety stock settings.
---

© 2025 Steadi, Inc. All rights reserved.