# ProdVerify

Counterfeit Product Detection and Warranty Tracking

ProdVerify is a web application designed to help manufacturers identify potentially counterfeit products and track warranty registrations using two unique QR codes for each physical product.

## Workflow

![ProdVerify workflow](docs/prodverify-workflow.png)

### 1. Product creation

The manufacturer creates a product record, assigns it to an intended authorized retailer, and generates two unique QR codes:

- **External QR:** Used by customers to verify the product before purchase.
- **Internal QR:** Used after purchase to register the product and activate its warranty.

For the MVP, the demo starts with three products—Product A, Product B, and Product C—each with its own product ID, external QR token, and internal QR token. This produces six unique QR codes.

### 2. Customer verification

The customer opens the external QR URL. The backend looks up the token in the database and returns the product details recorded by the manufacturer, including the intended retailer, product status, and scan count.

The system records verification attempts and can flag suspicious scan patterns or retailer mismatches when relevant evidence is available. A valid QR token alone does not prove that the physical item is genuine.

### 3. Warranty registration

After purchase, the customer opens the internal QR URL and submits the registration form. If the product is eligible and has not already been registered, the system records the registration, activates the warranty, and updates the product status to `SOLD`.

Duplicate registrations must be rejected.

## MVP features

- Manufacturer dashboard for products and QR codes
- Three demo products and six unique QR codes
- External QR verification
- Intended retailer information
- Scan history and scan-count calculation
- Suspicious-activity warnings
- Internal QR warranty registration
- Duplicate-registration prevention
- Warranty and product-status tracking

## Technology stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, TypeScript |
| Backend | Python, FastAPI |
| Database | SQLite (`counterfeit.db`) |
| Database access | SQLAlchemy |
| QR generation | Python `qrcode` and Pillow |

## Project structure

```text
ProdVerify/
├── ProdVerify_MVP_Specification.md
├── README.md
├── backend/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
├── frontend/
└── docs/
    └── prodverify-workflow.png
```

The exact file structure may change as implementation progresses.

## Database

The MVP uses five tables:

- `Manufacturers` — manufacturer records
- `Retailers` — authorized retailer and store-location records
- `Products` — physical product identity, QR tokens, intended retailer, and product status
- `Scan_History` — verification and registration scan events
- `Warranty_Registrations` — customer registration and warranty details

Scan counts should be calculated from `Scan_History` rather than maintained as a separate counter that could become inconsistent.

## Setup and running

The application is intended to run locally on Windows. The commands below assume the backend and frontend have been implemented as described in the project specification.

### Backend

Open a terminal in the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Initialize the database and seed data using the commands implemented by the project. For example, if the corresponding scripts exist:

```powershell
python -m app.init_db
python -m app.seed_data
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

Interactive API documentation: `http://127.0.0.1:8000/docs`

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite will display the local frontend URL in the terminal, commonly `http://localhost:5173`.

The initialization and seed commands must match the actual scripts created in the repository. Update this section if the implementation uses different command names.

## Verification scenarios

Before demonstrating the MVP, test these scenarios:

1. Product A, Product B, and Product C each have two unique QR codes.
2. Each external QR resolves to the correct product.
3. An unknown token returns an invalid-code result.
4. Verification scans are recorded and scan counts match scan history.
5. A retailer mismatch or suspicious scan pattern produces an explained warning when the required evidence is supplied.
6. A valid internal QR opens the registration form.
7. Successful registration activates the warranty and marks the product as `SOLD`.
8. A second registration attempt is rejected.
9. Dashboard values reflect persisted database records after refreshing the page.

## Limitations of the MVP

- A valid QR token and database record do not independently prove that the physical product is genuine; a QR code can be copied.
- The QR URL does not automatically reveal the customer's physical location. Location comparisons require reliable location evidence, such as an authenticated retailer flow or explicitly permitted geolocation.
- The MVP is intended for demonstration and requires additional authentication, security, monitoring, and deployment work before production use.

## Development specification

See [`ProdVerify_MVP_Specification.md`](ProdVerify_MVP_Specification.md) for the detailed MVP scope, schema, API requirements, workflow rules, and acceptance criteria.
