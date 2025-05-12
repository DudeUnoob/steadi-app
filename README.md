# Steadi

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

## Central SKU Repository

The Central SKU Repository is a core component of Steadi's inventory management system. It provides a robust, relational database structure for storing and tracking all inventory-related data with a complete audit trail.

### Key Features

- **Complete Audit Trail**: Every inventory mutation is recorded in the inventory ledger with source attribution (Shopify, Square, Lightspeed, CSV, manual, etc.)
- **SKU Normalization**: Canonical SKU storage ensures consistency across different sales channels and systems
- **Relational Structure**: Fully normalized database design with proper relationships between products, suppliers, and transactions
- **Search & Filter**: Fast, efficient searching and filtering capabilities for inventory management
- **Idempotent Operations**: Safe, repeatable inventory operations that prevent data inconsistencies

### API Endpoints

#### Inventory Management

- `GET /inventory` - Get paginated inventory with optional search
- `GET /inventory/{sku}` - Get product details by SKU
- `POST /inventory` - Create a new product
- `PATCH /inventory/{sku}` - Update product details
- `DELETE /inventory/{sku}` - Delete a product

#### Inventory Operations

- `POST /inventory/{sku}/update-quantity` - Update inventory quantity with audit trail
- `GET /inventory/{sku}/ledger` - Get inventory audit trail for a product

### Example API Usage

#### Get all inventory items
```bash
curl -X GET "http://localhost:8000/inventory?search=shirt&page=1&limit=50" \
  -H "Authorization: Bearer {your_access_token}" \
  -H "X-Tenant-ID: {tenant_id}" \
  -H "Content-Type: application/json"
```

#### Create a new product
```bash
curl -X POST "http://localhost:8000/inventory" \
  -H "Authorization: Bearer {your_access_token}" \
  -H "X-Tenant-ID: {tenant_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "SHIRT-BLK-M",
    "name": "Black T-Shirt",
    "variant": "Medium",
    "supplier_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "cost": 15.0,
    "on_hand": 50,
    "reorder_point": 10,
    "safety_stock": 5,
    "lead_time_days": 7
  }'
```

#### Update inventory quantity
```bash
curl -X POST "http://localhost:8000/inventory/SHIRT-BLK-M/update-quantity" \
  -H "Authorization: Bearer {your_access_token}" \
  -H "X-Tenant-ID: {tenant_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity_delta": -5,
    "source": "sale",
    "reference_id": "ORDER-12345"
  }'
```

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

### Docker Deployment (for later)

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

## Types
- feat: A new feature
- fix: A bug fix
- docs: Documentation changes only
- style: Changes that don't affect code functionality (formatting, etc.)
- refactor: Code changes that neither fix bugs nor add features
- test: Adding or modifying tests
- chore: Changes to build process, dependencies, etc.
- perf: Performance improvements

## Scope (Optional)
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

## Checking Out Branches
```
git checkout -b <your_name>/<feature_name>

git checkout main
git pull origin main
git checkout <your_name>/<feature_name>
git merge main

```

---

© 2025 Steadi, Inc. All rights reserved.

# Steadi - Role-Based Authentication

Implementation of the Role-Based Authentication component for the Steadi app, following the Product Requirements Document (PRD).

## Features

- JWT-based authentication
- Role-based access control (OWNER, MANAGER, STAFF)
- User registration and login
- Token refresh mechanism
- Integration with Neon PostgreSQL database

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi[all] sqlmodel psycopg2-binary python-jose[cryptography] passlib[bcrypt] uvicorn
```

2. Set up environment variables (or create a `.env` file):

```
DATABASE_URL=postgresql://neondb_owner:npg_fJaKY45kiMbh@ep-red-butterfly-a4516s6r-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
JWT_SECRET=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. Run the application:

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Endpoints

- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Login with email and password
- `POST /auth/refresh-token` - Get a new access token using refresh token
- `GET /auth/users/me` - Get current user information
- `POST /auth/users` - Create a new user (OWNER role required)

## Usage Examples

### Register a new user

```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "role": "STAFF"}'
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Access protected endpoint

```bash
curl -X GET "http://localhost:8000/auth/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Structure

- `app/` - Main application package
  - `main.py` - FastAPI application instance
  - `database.py` - Database connection and session management
  - `auth.py` - Authentication utilities (JWT, password hashing)
  - `models.py` - Data models and schemas
  - `routers/` - API route modules
    - `auth.py` - Authentication routes
- `main.py` - Application entry point

## 
.env needs:
'''
DATABASE_URL = postgresql://abcdefghijklmnop12345
'''