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

> **Important — always run every command from the project root (`ProdVerify/`) unless the step says otherwise.**
> The backend package is structured as `backend.app.*`, so Python must be started from the root so it can resolve the `backend` package. Running from inside `backend/` will cause `ModuleNotFoundError: No module named 'backend'`.

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

---

### Step 1 — Create the virtual environment

Open **Terminal 1** and navigate to the project root:

```powershell
# You should be at: ProdVerify/
python -m venv .venv
```

Activate the virtual environment (required for every new terminal session):

```powershell
# ProdVerify/
.\.venv\Scripts\Activate.ps1
```

> On first run, if PowerShell blocks scripts, run this once as Administrator:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Step 2 — Install backend dependencies

Still in **Terminal 1**, from the project root:

```powershell
# ProdVerify/
pip install -r backend\requirements.txt
```

---

### Step 3 — Initialize the database and seed data

Still in **Terminal 1**, from the project root:

```powershell
# ProdVerify/
.\.venv\Scripts\python.exe init_db.py
.\.venv\Scripts\python.exe seed_db.py
```

> Only run these once on a fresh install. Re-running `seed_db.py` on an existing database may insert duplicates.

---

### Step 4 — Start the backend API

Still in **Terminal 1**, from the project root:

```powershell
# ProdVerify/   ← must be the root, NOT backend/
.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000` | API base URL |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/health` | Health check |

**Leave Terminal 1 running.**

---

### Step 5 — Start the frontend

Open a **new Terminal 2**. Navigate to the `frontend/` subdirectory:

```powershell
# Open a brand new terminal window/tab
cd ProdVerify\frontend
npm install
npm run dev
```

You should see:

```
VITE v8.x.x  ready in ...ms
➜  Local:   http://127.0.0.1:5173/
```

**Leave Terminal 2 running.**

---

### Quick-start reference (after first-time setup)

Once you have done the setup once, starting the project only requires two terminals:

| Terminal | Directory | Command |
|---|---|---|
| **Terminal 1** (backend) | `ProdVerify/` | `.\.venv\Scripts\uvicorn.exe backend.app.main:app --reload --host 127.0.0.1 --port 8000` |
| **Terminal 2** (frontend) | `ProdVerify/frontend/` | `npm run dev` |

---

### Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Running uvicorn from `backend/` | `ModuleNotFoundError: No module named 'backend'` | Run from project root (`ProdVerify/`) |
| Using `python -m app.init_db` from `backend/` | `No module named app.init_db` | Use the root-level scripts `init_db.py` / `seed_db.py` instead |
| Using wrong pip (system Python instead of `.venv`) | Packages not found at runtime | Always activate `.venv` first or use `.\.venv\Scripts\pip.exe` explicitly |
| Frontend can't reach API | Network error / CORS in browser | Make sure the backend is running on port `8000` before starting the frontend |



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
