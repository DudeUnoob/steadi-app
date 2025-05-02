# **Steadi: Product Requirements Document for Phase 1 \- V2**

Below is a **first-pass Product-Requirements Document (PRD)** that an engineering squad can take straight into sprint planning. Everything that follows is intentionally explicit about field names, API routes, polling intervals, rate limits, and third-party dependencies.

---

# **1 Project Overview**

Steadi **Phase 1 MVP** delivers a laser-focused **retail inventory management** module (no marketing or delivery flows yet).

* **Frontend** – single-page React 18 \+ Vite (JS) app.  
* **Backend** – FastAPI 0.110+, PostgreSQL 16, Redis 7, AWS Lambda for scheduled jobs, JWT auth.  
* **Connectors** – Shopify GraphQL Admin API, Square Inventory API, Lightspeed Retail API, plus CSV upload.  
* **Hosting/ops** – AWS (API Gateway → Lambda/FastAPI on Fargate), Terraform IaC, GitHub Actions CI/CD, CloudWatch alerts.

Success \= three pilot boutiques run Steadi daily with \<200 ms dashboard loads and \<10 % logo-churn after 90 days. (See product-roadmap file for schedule milestones ).

# **2\. Features (Phase 1\)**

| \# | Feature | One-line value prop |
| ----- | ----- | ----- |
| 1 | Owner Dashboard | Live table \+ mini-charts; fast UX (“Excel-speed”). |
| 2 | POS \+ CSV Connectors | 15-minute idempotent sync from Shopify/Square/Lightspeed or CSV. |
| 3 | Central SKU Repository | Normalised catalog with full audit trail. |
| 4 | Stock-Threshold Engine | Background rule evaluates ROP per SKU. |
| 5 | Actionable Stock Alerts | Email \+ in-app toast when stock \< ROP. |
| 6 | One-Click PO Generation | Draft PDF \+ supplier-addressed email in one action. |
| 7 | Re-order Tracker | PO Kanban (Draft → Sent → Received). |
| 8 | Role-based Auth | JWT (Owner / Manager / Staff). |
| 9 | Essential Analytics | Turnover rate, top-sellers, days-of-stock-left. |
| 10 | Config & Supplier Dir | CRUD for suppliers, thresholds, connector tokens. |
| 11 | Notification Svc | Centralised email \+ rate-limit (100 req/min). |
| 12 | Serverless/DevOps | IaC, CI/CD, logging, monitoring. |

---

# 

# **3 Detailed Requirements**

**Must Have**

## **3.1 Owner Dashboard**

* **Functional**

/api/dashboard/inventory?search=\&page=\&limit= returns items:\[{sku, name,on\_hand, reorder\_point, badge,color}\].

* Column resize \+ virtualised list (TanStack Table).

  * Mini line graph for last 7 days sales (/api/analytics/sales?period=7d).

* **NFR** – Initial load ≤ 200 ms, search filter updates ≤ 100 ms.

* **Dependencies** – React 18, TanStack Query, D3 or Recharts for spark-lines.

## **3.2 Central SKU Repository**

* Fully relational—see §4 Data Models.

* Every external mutation inserts into inventory\_ledger with source \= shopify|square|lightspeed|csv.

## **3.3 Automated Stock-Threshold Engine**

* Lambda threshold\_evaluator runs every 15 min.

* Formula: reorder\_point \= safety\_stock \+ (avg\_daily\_sales × lead\_time\_days); values overridable per SKU.

* If on\_hand ≤ reorder\_point set alert\_level \= 'RED'; if on\_hand ≤ reorder\_point \+ safety\_stock \=\> YELLOW.

## 

## **3.4 Role-Based Authentication**

* Libraries: python-jose \+ passlib. Example FastAPI JWT flow ([Implementing Secure User Authentication in FastAPI using JWT ...](https://neon.tech/guides/fastapi-jwt?utm_source=chatgpt.com), [Securing FastAPI with JWT Token-based Authentication | TestDriven.io](https://testdriven.io/blog/fastapi-jwt-auth/?utm_source=chatgpt.com)).

* Token payload:

{ "sub":"user\_1", "role":"OWNER", "exp":1699999999 }

* Owner can CRUD connectors; Staff \= read-only inventory.

**Should Have**

## **3.5 POS & CSV Connectors**

* **Shopify** – Use inventoryLevel query to pull availableQuantity per inventoryItemId ([inventoryLevel \- GraphQL Admin \- Shopify.dev](https://shopify.dev/docs/api/admin-graphql/latest/queries/inventoryLevel?utm_source=chatgpt.com), [InventoryLevel \- GraphQL Admin \- Shopify.dev](https://shopify.dev/docs/api/admin-graphql/2024-10/objects/InventoryLevel?utm_source=chatgpt.com)).

* **Square** – Poll GET /v2/inventory/changes/batch-retrieve (API version 2025-04-16) ([Inventory API \- Square API Reference \- Square Developer](https://developer.squareup.com/reference/square/inventory-api?utm_source=chatgpt.com), [POST /v2/inventory/changes/batch-retrieve \- Square API Reference](https://developer.squareup.com/reference/square/inventory-api/batch-retrieve-inventory-changes?utm_source=chatgpt.com)).

* **Lightspeed** – REST endpoint GET /API/Account/{accountID}/Item/{itemID}.json ([Integrating with the Lightspeed Retail POS (R-Series) API](https://retail-support.lightspeedhq.com/hc/en-us/articles/229129268-Integrating-with-the-Lightspeed-Retail-POS-R-Series-API?utm_source=chatgpt.com), [Lightspeed Retail API](https://retail-support.lightspeedhq.com/hc/en-us/sections/8332641559323-Lightspeed-Retail-API?utm_source=chatgpt.com)).

* CSV wizard maps sku, name, on\_hand, cost, supplier\_name.

* **Sync cadence** – AWS EventBridge rule rate(15 minutes) triggers sync\_handler Lambda ([Invoke a Lambda function on a schedule \- AWS Documentation](https://docs.aws.amazon.com/lambda/latest/dg/with-eventbridge-scheduler.html?utm_source=chatgpt.com), [Create an EventBridge scheduled rule for AWS Lambda functions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html?utm_source=chatgpt.com)).

* **Field normalisation** – store canonical SKU in products.sku (VARCHAR 64, unique).

## **3.6 Actionable Stock Alerts**

* Compose message: "Reorder {reorder\_qty} × '{sku}' – Est. {days\_left} days left".

* Channels: email, in\_app.

* Rate-limit service enforces 100 req/min across tenant.

## **3.7 One-Click PO Generation**

* Endpoint: POST /purchase-orders payload

{  
  "supplier\_id": "sup\_123",  
  "lines": \[{ "sku": "CNDL-003", "qty": 15 }\],  
  "send\_email": true  
}

* Returns pdf\_url and status='SENT' when send\_email=true.

* PDF template uses @react-pdf/renderer on backend.

* Email via SendGrid (env SENDGRID\_API\_KEY).

## **3.8 Essential Analytics**

* Redis key pattern analytics:{tenant\_id}:{metric}:{period} (TTL \= 5 min).

* Server computes:

  * turnover\_rate \= cost\_of\_goods\_sold ÷ avg\_inventory\_value.

  * days\_of\_stock \= on\_hand ÷ avg\_daily\_sales.

**Could Have**

## **3.9 Re-order Workflow Tracker**

* PATCH /purchase-orders/{id} with { "status": "RECEIVED" } auto-increments products.on\_hand and logs ledger row (source='po\_receive').

### 

### **3.10 Config & Supplier Directory**

* **CRUD Endpoints**: Complete supplier management API  
* **Configuration**: Threshold management via PATCH endpoint  
* **Parameters**: Support for min\_qty, max\_qty, and lead\_time\_days configuration

## **3.11 Config & Supplier Directory**

* Endpoints:

  * GET /suppliers, POST /suppliers, PATCH /suppliers/{id}, DELETE ….

  * PATCH /products/{sku}/thresholds to update min\_qty, max\_qty, lead\_time\_days.

**Won’t Have**

## **3.12 Notification & Rate-Limiting Service**

* Microservice listens on Redis stream notifications\_out.

* If sent\_count(window=1m) ≥ 100 → reject publish with 429.

## **3.13 Serverless Foundations & Dev Ops**

* Terraform modules: networking, ecs\_cluster, rds\_postgres, eventbridge\_rules.

* GitHub-actions workflow:

  * on: push → run pytest, npm run test, build Docker image, deploy to ECR, Terraform apply.

* CloudWatch alarm when p95 latency \> 500 ms for 5 mins.

# **4 Classes to Implement**

---

## **4.1 Enums**

class AlertLevel(str, Enum):  
    RED \= "RED"  
    YELLOW \= "YELLOW"

class UserRole(str, Enum):  
    OWNER \= "OWNER"  
    MANAGER \= "MANAGER"  
    STAFF \= "STAFF"

class POStatus(str, Enum):  
    DRAFT \= "DRAFT"  
    SENT \= "SENT"  
    RECEIVED \= "RECEIVED"

class ConnectorProvider(str, Enum):  
    SHOPIFY \= "SHOPIFY"  
    SQUARE \= "SQUARE"  
    LIGHTSPEED \= "LIGHTSPEED"  
    CSV \= "CSV"

class NotificationChannel(str, Enum):  
    EMAIL \= "EMAIL"  
    IN\_APP \= "IN\_APP"  
    SMS \= “SMS”

## **4.2 Data Models**

 class User(SQLModel, table=True):  
    """User account with authentication and authorization"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    email: str \= Field(unique=True, index=True)  
    password\_hash: str  
    role: UserRole \= Field(default=UserRole.STAFF)  
    created\_at: datetime \= Field(default\_factory=datetime.utcnow)  
    \# Relationships  
    notifications: List\["Notification"\] \= Relationship(back\_populates="user")

class Supplier(SQLModel, table=True):  
    """Supplier or vendor information"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    name: str \= Field(index=True)  
    contact\_email: str  
    phone: Optional\[str\] \= None  
    lead\_time\_days: int \= Field(default=7)  
    \# Relationships  
    products: List\["Product"\] \= Relationship(back\_populates="supplier")  
    purchase\_orders: List\["PurchaseOrder"\] \= Relationship(back\_populates="supplier")

class Product(SQLModel, table=True):  
    """Inventory item with stock levels and thresholds"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    sku: str \= Field(unique=True, index=True)  
    name: str \= Field(index=True)  
    variant: Optional\[str\] \= None  
    supplier\_id: Optional\[UUID\] \= Field(default=None, foreign\_key="supplier.id")  
    cost: float \= Field(ge=0)  
    on\_hand: int \= Field(default=0, ge=0)  
    reorder\_point: int \= Field(default=0, ge=0)  
    safety\_stock: int \= Field(default=0, ge=0)  
    lead\_time\_days: int \= Field(default=7, ge=1)  
    created\_at: datetime \= Field(default\_factory=datetime.utcnow)  
    alert\_level: Optional\[AlertLevel\] \= None  
    \# Relationships  
    supplier: Optional\[Supplier\] \= Relationship(back\_populates="products")  
    ledger\_entries: List\["InventoryLedger"\] \= Relationship(back\_populates="product")  
    sales: List\["Sale"\] \= Relationship(back\_populates="product")  
    purchase\_order\_items: List\["PurchaseOrderItem"\] \= Relationship(back\_populates="product")

class InventoryLedger(SQLModel, table=True):  
    """Audit trail for all inventory changes"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    product\_id: UUID \= Field(foreign\_key="product.id")  
    quantity\_delta: int  
    quantity\_after: int  
    source: str \= Field(index=True)  \# shopify, square, lightspeed, csv, po\_receive, manual  
    reference\_id: Optional\[str\] \= None  
    timestamp: datetime \= Field(default\_factory=datetime.utcnow)  
    \# Relationships  
    product: Product \= Relationship(back\_populates="ledger\_entries")

class Sale(SQLModel, table=True):  
    """Record of product sales for analytics"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    product\_id: UUID \= Field(foreign\_key="product.id", index=True)  
    quantity: int \= Field(gt=0)  
    sale\_date: datetime \= Field(default\_factory=datetime.utcnow, index=True)  
    \# Relationships  
    product: Product \= Relationship(back\_populates="sales")

class PurchaseOrder(SQLModel, table=True):  
    """Order to suppliers for inventory replenishment"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    supplier\_id: UUID \= Field(foreign\_key="supplier.id", index=True)  
    status: POStatus \= Field(default=POStatus.DRAFT, index=True)  
    created\_by: UUID \= Field(foreign\_key="user.id")  
    pdf\_url: Optional\[str\] \= None  
    created\_at: datetime \= Field(default\_factory=datetime.utcnow)  
    updated\_at: datetime \= Field(default\_factory=datetime.utcnow)  
    \# Relationships  
    supplier: Supplier \= Relationship(back\_populates="purchase\_orders")  
    items: List\["PurchaseOrderItem"\] \= Relationship(back\_populates="purchase\_order")

class PurchaseOrderItem(SQLModel, table=True):  
    """Line item in a purchase order"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    po\_id: UUID \= Field(foreign\_key="purchaseorder.id")  
    product\_id: UUID \= Field(foreign\_key="product.id")  
    quantity: int \= Field(gt=0)  
    unit\_cost: float \= Field(ge=0)  
    \# Relationships  
    purchase\_order: PurchaseOrder \= Relationship(back\_populates="items")  
    product: Product \= Relationship(back\_populates="purchase\_order\_items")

class Connector(SQLModel, table=True):  
    """Integration with external POS/inventory systems"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    provider: ConnectorProvider  
    access\_token: str  
    refresh\_token: Optional\[str\] \= None  
    expires\_at: Optional\[datetime\] \= None  
    status: str \= Field(default="ACTIVE")  
    created\_by: UUID \= Field(foreign\_key="user.id")  
    last\_sync: Optional\[datetime\] \= None

class Notification(SQLModel, table=True):  
    """User notifications for alerts and events"""  
    id: Optional\[UUID\] \= Field(default=None, primary\_key=True)  
    user\_id: UUID \= Field(foreign\_key="user.id")  
    channel: NotificationChannel  
    payload: Dict \= Field(default={})  
    sent\_at: Optional\[datetime\] \= Field(default\_factory=datetime.utcnow)  
    read\_at: Optional\[datetime\] \= None  
    \# Relationships  
    user: User \= Relationship(back\_populates="notifications")

## **4.3 Service Classes**

class InventoryService:  
    """Manages inventory operations and ledger entries"""  
      
    def update\_inventory(self, sku: str, quantity\_delta: int, source: str, reference\_id: Optional\[str\] \= None) \-\> Product:  
        """Update inventory levels with audit trail"""  
        pass  
      
    def get\_inventory(self, search: Optional\[str\] \= None, page: int \= 1, limit: int \= 50\) \-\> Dict\[str, Union\[List\[Product\], int\]\]:  
        """Get paginated inventory with search"""  
        pass  
      
    def get\_ledger(self, product\_id: UUID, start\_date: Optional\[datetime\] \= None, end\_date: Optional\[datetime\] \= None) \-\> List\[InventoryLedger\]:  
        """Get inventory audit trail for a product"""  
        pass

class ThresholdService:  
    """Evaluates inventory thresholds and generates alerts"""  
      
    def evaluate\_thresholds(self, product\_id: Optional\[UUID\] \= None) \-\> List\[Dict\]:  
        """Evaluate thresholds for one or all products"""  
        pass  
      
    def calculate\_reorder\_point(self, product\_id: UUID) \-\> int:  
        """Calculate reorder point based on formula"""  
        pass  
      
    def calculate\_days\_of\_stock(self, product\_id: UUID) \-\> float:  
        """Calculate estimated days of stock remaining"""  
        pass

class AlertService:  
    """Manages stock alerts and notifications"""  
      
    def generate\_alert(self, product\_id: UUID, alert\_level: AlertLevel) \-\> Dict:  
        """Generate alert for low stock"""  
        pass  
      
    def send\_notification(self, user\_id: UUID, channel: NotificationChannel, payload: Dict) \-\> Notification:  
        """Send notification through specified channel"""  
        pass  
      
    def check\_rate\_limit(self, tenant\_id: str) \-\> bool:  
        """Check if notifications are within rate limit"""  
        pass

class PurchaseOrderService:  
    """Manages purchase order creation and workflow"""  
      
    def create\_purchase\_order(self, supplier\_id: UUID, lines: List\[Dict\], send\_email: bool \= False) \-\> PurchaseOrder:  
        """Create a purchase order with optional email"""  
        pass  
      
    def generate\_pdf(self, purchase\_order\_id: UUID) \-\> str:  
        """Generate PDF for purchase order"""  
        pass  
      
    def update\_status(self, purchase\_order\_id: UUID, status: POStatus) \-\> PurchaseOrder:  
        """Update purchase order status"""  
        Pass  
class ConnectorService:  
    """Manages external system connections and synchronization"""  
      
    def sync\_shopify(self, connector\_id: UUID) \-\> Dict:  
        """Sync inventory from Shopify"""  
        pass  
      
    def sync\_square(self, connector\_id: UUID) \-\> Dict:  
        """Sync inventory from Square"""  
        pass  
      
    def sync\_lightspeed(self, connector\_id: UUID) \-\> Dict:  
        """Sync inventory from Lightspeed"""  
        pass  
      
    def import\_csv(self, file\_path: str, mapping: Dict) \-\> Dict:  
        """Import inventory from CSV file"""  
        pass

class AnalyticsService:  
    """Computes and caches business analytics"""  
      
    def calculate\_turnover\_rate(self, product\_id: Optional\[UUID\] \= None, period: int \= 30\) \-\> Dict:  
        """Calculate inventory turnover rate"""  
        pass  
      
    def get\_top\_sellers(self, limit: int \= 10, period: int \= 30\) \-\> List\[Dict\]:  
        """Get top selling products"""  
        pass  
      
    def get\_sales\_history(self, product\_id: UUID, period: int \= 7\) \-\> List\[Dict\]:  
        """Get sales history for product"""  
        pass

# **5 Data Models (PostgreSQL)** 

We’ll be using: sqlmodel import SQLModel, create\_engine, Session 

| Table | Key columns (type) | Notes |
| ----- | ----- | ----- |
| **users** | id UUID PK, email VARCHAR(256) unique, password\_hash, role ENUM('OWNER','MANAGER','STAFF'), created\_at TIMESTAMPTZ |  |
| **suppliers** | id UUID PK, name, contact\_email, phone, lead\_time\_days INT |  |
| **products** | id UUID PK, sku VARCHAR(64) unique, name, variant, supplier\_id FK, cost NUMERIC(10,2), on\_hand INT, reorder\_point INT, safety\_stock INT, lead\_time\_days INT, created\_at |  |
| **inventory\_ledger** | id UUID PK, product\_id FK, quantity\_delta INT, quantity\_after INT, source VARCHAR(32), reference\_id VARCHAR(64), ts TIMESTAMPTZ | Full history/audit |
| **purchase\_orders** | id UUID PK, supplier\_id FK, status ENUM('DRAFT','SENT','RECEIVED'), created\_by FK users, pdf\_url TEXT, created\_at, updated\_at |  |
| **po\_items** | id UUID PK, po\_id FK, product\_id FK, qty INT, unit\_cost NUMERIC(10,2) |  |
| **connectors** | id UUID PK, provider ENUM('SHOPIFY','SQUARE','LIGHTSPEED','CSV'), access\_token TEXT, refresh\_token TEXT, expires\_at TIMESTAMPTZ, status ENUM('ACTIVE','ERROR'), created\_by FK users |  |
| **notifications** | id UUID PK, user\_id FK, channel ENUM('EMAIL','IN\_APP'), payload JSONB, sent\_at, read\_at |  |
| **analytics\_cache** | id UUID PK, metric VARCHAR(64), value JSONB, generated\_at |  |

All timestamp columns use UTC. All FK actions ON DELETE CASCADE unless otherwise noted.

---

# **6 API Contract (FastAPI path \+ schema)**

POST /auth/signup  
  body { email, password }  
  201 \=\> { token, refresh\_token }

POST /auth/login  
  body { email, password }  
  200 \=\> { token, refresh\_token }

GET /inventory  
  query { search, page=1, limit=50 }  
  200 \=\> { items:\[ProductOut\], total }

PATCH /inventory/{sku}  
  body { on\_hand?, reorder\_point?, safety\_stock? }

POST /connectors  
  body { provider, oauth\_code }  
  202 \=\> { status:'PENDING' }   \# OAuth callback completes token exchange

POST /purchase-orders  
  body { supplier\_id, lines:\[{sku, qty}\], send\_email }  
  201 \=\> { id, pdf\_url, status }

PATCH /purchase-orders/{id}  
  body { status }   \# accepted values: SENT, RECEIVED

GET /analytics/metrics  
  query { period=30d }  
  200 \=\> { turnover\_rate, top\_sellers:\[{sku, qty}\], days\_of\_stock\_left }

GET /notifications  
  200 \=\> { items:\[NotificationOut\] }

**Common headers**

Authorization: Bearer \<JWT\>  
X-Tenant-ID: \<store\_uuid\>  \# multi-tenant isolation  
Content-Type: application/json

**Error shape**

{ "error": { "code": "RESOURCE\_NOT\_FOUND", "message": "Product not found" } }

Standard codes: 400, 401, 403, 404, 409, 422, 500\.

---

# **7 Dependencies & Env Vars**

| Layer | Package / Service | Version / note |
| ----- | ----- | ----- |
| Frontend | react@18, vite@5, @tanstack/react-query, tailwindcss@3, recharts |  |
| Backend | fastapi@0.110, uvicorn\[standard\], sqlmodel, python-jose, passlib\[bcrypt\], aiohttp, boto3, redis-py |  |
| AWS | us-east-1 – RDS Postgres 16, Lambda runtime python3.12, EventBridge Scheduler |  |
| Integrations | Shopify (GraphQL Admin API, scopes read\_inventory,read\_products), Square (Inventory API v2025-04-16), Lightspeed Retail API v2025 R-series, SendGrid v3 mail API |  |

Environment variables (backend):

DATABASE\_URL=postgresql+psycopg2://...  
REDIS\_URL=redis://...  
JWT\_SECRET=supersecret  
SHOPIFY\_API\_KEY=...  
SQUARE\_ACCESS\_TOKEN=...  
LIGHTSPEED\_CLIENT\_ID=...  
SENDGRID\_API\_KEY=...

---

# **8 Open Questions / Next Steps**

1. **UX mocks** – need Figma wireframes before sprint 3\.

2. **CSV import edge-cases** – decide how to handle duplicate SKUs vs. variants.

3. **PDF template design** – marketing/ops to supply brand assets.

4. **SOC-2 logging** – confirm retention window (default 90 days).

Feel free to iterate or drill deeper on any slice (e.g., analytics formulas, auth flows). Once the team signs off, these sections can be copied verbatim into Jira tickets and Terraform modules.

## **9 Use Cases**

---

**1\. Maya \- Boutique Clothing Store Owner**

**Persona:** Maya (35) owns a small fashion boutique with two employees. She has minimal technical expertise but needs to maintain inventory across 300+ SKUs with seasonal variations. She's often overwhelmed by ordering decisions and frequently discovers out-of-stock situations too late, losing sales.

**Use Case: Emergency Stock Replenishment** Maya receives a Steadi notification while helping a customer: "Reorder 12 × 'BLK-DRESS-S' – Est. 3 days left." She taps the notification to see that her popular black dresses in size small are almost gone. Using the one-click PO feature, she immediately sends a purchase order to her supplier without interrupting her customer interaction. Four days later, she receives the shipment and updates inventory by simply scanning the received items, with Steadi automatically updating stock levels.

## **2\. Carlos \- Craft Brewery Manager**

**Persona:** Carlos (42) manages a small craft brewery with a retail storefront. He juggles production schedules with inventory management for both raw materials (hops, malt, bottles) and finished products. His current system involves spreadsheets that are rarely up-to-date, causing production delays when ingredients run short.

**Use Case: Multi-location Inventory Sync** Carlos uses Steadi to connect his Square POS system in the taproom with his production inventory managed in a separate system. When customers purchase beer in the taproom, Steadi automatically reduces finished product inventory and calculates when raw materials for the next batch will need to be ordered. When approaching the reorder threshold for hops, Steadi sends Carlos an alert: "Reorder 25kg × 'CITRA-HOPS' – Est. 7 days left before production impact." Carlos approves the PO from his phone while on the brewery floor, ensuring production continues without interruption.

## **3\. Priya \- Home Goods Store Manager**

**Persona:** Priya (28) manages a home goods store with 5 employees. She's tech-savvy but time-constrained, handling everything from staff scheduling to inventory. She struggles with seasonal demand fluctuations and limited storage space, making optimal stocking decisions crucial.

**Use Case: Seasonal Trend Analysis** Looking at Steadi's analytics dashboard, Priya notices the system has flagged several seasonal items with the "YELLOW" alert level. Reviewing the turnover rate metrics, she sees that certain decorative items are selling 40% faster than the same period last year. Instead of following the system's standard recommendation to reorder the minimum quantity, she uses the analytics data to adjust her order quantity upward, ensuring she doesn't miss sales during the upcoming holiday season. Steadi's dashboard allows her to make this decision in minutes rather than the hours it previously took to analyze sales data manually.

## **4\. Raj \- Specialty Grocery Store Owner**

**Persona:** Raj (50) owns a specialty grocery store focusing on international foods. He manages thousands of SKUs with varying shelf lives and supply chain complexities. He struggles with balancing fresh inventory against waste and maintaining stock of rare imported items with unpredictable lead times.

**Use Case: Supplier Management** Raj receives a Steadi alert about multiple products from the same international supplier approaching reorder points. Using the supplier directory, he pulls up all products from this vendor and sees that seven items need reordering. Since this supplier has a 21-day lead time (as configured in Steadi), the system has calculated the optimal time to place orders. Raj uses Steadi's batch PO feature to create a single order for all items, maximizing his shipping efficiency. He then adjusts the thresholds for seasonal items in anticipation of upcoming holidays, allowing Steadi to more accurately calculate reorder points based on the adjusted lead times and safety stock levels.

## **5\. Aisha \- Artisanal Soap Workshop Owner**

**Persona:** Aisha (31) runs a growing artisanal soap business that sells through her Shopify store, local farmers markets, and wholesale to small retailers. She makes all products in small batches and struggles to track inventory across multiple sales channels, often discovering discrepancies too late.

**Use Case: Multi-channel Inventory Reconciliation** After a busy weekend of sales across multiple channels, Aisha opens Steadi to reconcile her inventory. The system has automatically synchronized sales data from her Shopify store, but she needs to manually enter the farmers market sales via CSV upload. After uploading, Steadi identifies a discrepancy between physical counts and system records for two products. The inventory ledger feature allows her to trace all transactions for these products, identifying that a wholesale order was incorrectly entered. She corrects the entry, and Steadi recalculates her stock levels and adjusts the reorder forecasts accordingly. The dashboard now shows accurate days-of-stock-left metrics for all products, with alerts for ingredients that need to be ordered for her next production batch.

These personas and use cases illustrate how different small business owners would interact with Steadi's features to solve real inventory management challenges, highlighting the value proposition of the product.

