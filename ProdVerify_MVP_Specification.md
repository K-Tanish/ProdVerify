# ProdVerify --- MVP Project Specification

## 1. Project overview

**ProdVerify** is a counterfeit-product detection and warranty-tracking
web application.

The MVP helps a customer check a product's recorded identity and
intended selling location before purchase, then register the product and
activate its warranty after purchase.

The system uses two unique QR codes per physical product:

-   **External QR:** used for pre-purchase verification.
-   **Internal QR:** used for post-purchase warranty registration.

The QR code contains a URL with a unique token. The backend uses that
token to retrieve the corresponding product and its current database
records. Product details and mutable state must not be trusted from data
printed inside the QR code.

## 2. MVP technology stack

-   **Frontend:** React + Vite + TypeScript
-   **Backend:** Python + FastAPI
-   **ORM/database access:** SQLAlchemy
-   **Database:** SQLite, stored locally as `counterfeit.db`
-   **QR generation:** Python `qrcode` and Pillow
-   **Token generation:** Python `secrets` (cryptographically secure
    random tokens)

The MVP should run locally on Windows. Do not require PostgreSQL, a
cloud service, an LLM, blockchain, or microservices.

## 3. Minimal demonstration scenario

One demo manufacturer creates exactly three individual product records:

-   Product A
-   Product B
-   Product C

Each product has: - One unique product ID - One unique serial number -
One unique external QR token - One unique internal QR token - One
intended authorized retailer - A product status

Therefore, the initial demo has **3 products and 6 unique QR codes**.

  -----------------------------------------------------------------------
  Product           Example product   External QR       Internal QR
                    ID                purpose           purpose
  ----------------- ----------------- ----------------- -----------------
  Product A         `PROD-001`        Verify Product A  Register Product
                                                        A

  Product B         `PROD-002`        Verify Product B  Register Product
                                                        B

  Product C         `PROD-003`        Verify Product C  Register Product
                                                        C
  -----------------------------------------------------------------------

These product IDs are illustrative. Use database-generated IDs or stable
demo identifiers consistently.

Generate independent, cryptographically random external and internal
tokens. Store the tokens in the database and generate QR images from
URLs such as:

-   `http://<reachable-host>/verify/<external-token>`
-   `http://<reachable-host>/register/<internal-token>`

Use a configurable base URL. Do not hardcode `localhost` into QR codes
if the codes will be scanned from another device.

## 4. User roles

### Manufacturer (MVP demo)

-   View an overview dashboard.
-   Create and view products.
-   Assign an intended retailer.
-   Generate and download both QR images for each product.
-   View scan history and scan counts.
-   View warranty registrations and suspicious events.

For the local MVP, manufacturer authentication may be omitted or
simplified, but administrative endpoints should be separated from public
customer endpoints and structured so authentication can be added later.

### Customer

-   Open/scan an external QR and see the verification result.
-   View product identity, intended retailer/location, scan count,
    product/registration status, and any warning.
-   Open/scan an internal QR and submit the warranty registration form
    after purchase.

## 5. Database schema

Create these five tables with primary keys, foreign keys, uniqueness
constraints, validation, and useful indexes.

### `Manufacturers`

-   `manufacturer_id`: primary key
-   `manufacturer_name`: required
-   `contact_email`
-   `status`

### `Retailers`

-   `retailer_id`: primary key
-   `retailer_name`: required
-   `address`
-   `city`
-   `state`
-   `status`

### `Products`

-   `product_id`: primary key
-   `product_name`: required
-   `manufacturer_id`: foreign key
-   `serial_number`: unique
-   `external_qr_token`: unique
-   `internal_qr_token`: unique
-   `manufacturing_location`
-   `intended_retailer_id`: foreign key to `Retailers`
-   `product_status`: `IN_STOCK`, `SOLD`, or `BLOCKED`
-   `created_at`

Each physical unit has its own product record. The two QR tokens map to
the same product, but invoke different workflows. Enforce that the
external and internal token for a product differ. Generate tokens
securely and retry if a collision occurs.

### `Scan_History`

-   `scan_id`: primary key
-   `product_id`: nullable foreign key to `Products`, so unknown-token
    attempts can also be logged
-   `scan_type`: `EXTERNAL_VERIFICATION` or `INTERNAL_REGISTRATION`
-   `scanned_at`
-   `scan_location`: nullable
-   `result`
-   `risk_reason`: nullable

Calculate scan counts from scan-history records rather than keeping a
second, potentially inconsistent counter in `Products`. Record failed
attempts without storing raw secret tokens unnecessarily.

### `Warranty_Registrations`

-   `registration_id`: primary key
-   `product_id`: unique foreign key to `Products`
-   `customer_name`
-   `email`
-   `retailer_id`: foreign key to `Retailers`
-   `purchase_price`
-   `purchase_date`
-   `warranty_status`: `ACTIVE`, `EXPIRED`, or `VOID`
-   `warranty_start_date`
-   `warranty_end_date`

The MVP permits only one initial warranty registration per physical
product.

## 6. External QR verification workflow

1.  Customer opens `/verify/{external_token}`.
2.  Backend looks up the token in `Products`.
3.  If no product matches, return `INVALID` and record the failed
    attempt where feasible.
4.  If a product matches, retrieve its identity, intended retailer,
    product status, registration status, and prior scan history.
5.  Record the current verification attempt in `Scan_History`.
6.  Calculate the external verification scan count without counting the
    current scan twice.
7.  Evaluate the available evidence and return a result with an
    explanation.

Use these result categories:

-   **VERIFIED:** valid product record and no detected warning in the
    available evidence.
-   **SUSPICIOUS:** valid token but a concerning product state, retailer
    mismatch, or suspicious scan pattern.
-   **INVALID:** token does not match a known product.

A valid QR/database match does not prove the physical item is genuine.
Explain that the result is based on the manufacturer's recorded data and
the risk indicators available to the system.

### Location limitation

The external QR reveals the intended retailer from the database; it does
not automatically reveal the customer's physical location.

For the MVP, use a customer-selected retailer or retailer-specific
verification link as location evidence. Clearly label self-reported
information. Do not claim GPS verification unless permission was granted
and coordinates were actually obtained. A mismatch should trigger a
warning, not automatically prove counterfeiting.

### Scan-risk logic

Use a configurable scan threshold and scan history to flag unusual
patterns. Repeated scans alone are not proof of counterfeiting; show an
explanation for every warning.

## 7. Internal QR and warranty registration workflow

1.  Customer opens `/register/{internal_token}`.
2.  Backend resolves the internal token to a product.
3.  Reject an invalid token.
4.  Check product eligibility and whether it is already registered or
    blocked.
5.  Show a form for customer name, email, retailer, purchase price, and
    purchase date.
6.  Validate the submitted data.
7.  Create the warranty registration.
8.  Set product status to `SOLD` and activate the warranty with
    configured start/end dates.
9.  Record the registration attempt in scan history.
10. Show a confirmation page with registration and warranty details.

Perform registration, product status change, and successful scan logging
in one database transaction. Enforce uniqueness at the database level
and safely reject duplicate or concurrent registrations.

Scanning the internal QR initiates the workflow; warranty activation
occurs only after valid registration details are submitted. Warranty
duration should be configurable, with a demo default.

## 8. Required API endpoints

Manufacturer/admin: - `POST /api/products` - `GET /api/products` -
`GET /api/products/{product_id}` -
`GET /api/products/{product_id}/qrs` - `GET /api/scans` -
`GET /api/warranties` - `GET /api/dashboard/stats`

Customer: - `GET /api/verify/{token}` - `POST /api/register/{token}`

Also include a health endpoint. Use appropriate HTTP status codes,
validated request/response schemas, and structured error messages.

## 9. Dashboard requirements

Dashboard metrics must be derived from database records, not
hardcoded: - Total products - In-stock products - Sold products - Active
warranty registrations - Total external verification scans - Suspicious
scans/events

Include: - Product table with search/filter - QR preview and separate
download controls - Scan-history table with filters -
Warranty-registration table with filters - Clear warnings and
verification result labels

## 10. Seed data

Provide a repeatable development seed command/script that creates: - One
demo manufacturer - Two demo retailers in different locations - Exactly
three initial products (A, B, C) - Six unique tokens, two per product -
QR images generated from the stored tokens

Running the seed process more than once must not create duplicate
products or QR tokens. Do not silently overwrite existing data.

## 11. Acceptance tests

The MVP is ready for demonstration when:

1.  Products A, B, and C exist in the database.
2.  Exactly six unique QR tokens are generated for those three products.
3.  Each QR resolves to the correct product.
4.  A valid external QR shows product and intended retailer details.
5.  An unknown token returns `INVALID`.
6.  Every verification attempt is logged.
7.  The scan count matches the stored scan-history records.
8.  An unexpected retailer produces an appropriately qualified warning
    when evidence is supplied.
9.  Suspicious scan patterns produce an explainable warning.
10. A valid internal QR opens the registration form.
11. Successful registration activates the warranty and marks the product
    `SOLD`.
12. A second registration attempt is rejected.
13. Invalid registration data does not partially update the database.
14. Dashboard metrics reflect real database values.
15. The application runs locally on Windows using documented commands.

## 12. Development constraints

-   Inspect the workspace before editing files.
-   Implement incrementally and run tests after each checkpoint.
-   Keep frontend, backend, database models, schemas, and business logic
    organized.
-   Do not substitute mock responses for core workflows.
-   Do not add unrelated features before the MVP works.
-   Report commands run, files changed, test results, and unresolved
    errors honestly.
-   Document how to run the backend and frontend in separate terminals.
-   Prioritize an end-to-end working prototype over premature production
    infrastructure.
