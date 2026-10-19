const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Retailer {
  retailer_id: number;
  retailer_name: string;
  address?: string | null;
  city: string;
  state: string;
  status: string;
}

export interface Product {
  product_id: string;
  product_name: string;
  serial_number: string;
  product_status: 'IN_STOCK' | 'SOLD' | 'BLOCKED';
  manufacturing_location?: string | null;
  external_qr_token: string;
  internal_qr_token: string;
  registration_status: string;
  intended_retailer?: {
    retailer_id: number;
    retailer_name: string;
    city?: string;
    state?: string;
  } | null;
  created_at?: string | null;
}

export interface ScanEvent {
  scan_id: number;
  product_id: string | null;
  product_name: string | null;
  scan_type: string;
  scanned_at: string;
  scan_location: string | null;
  result: 'VERIFIED' | 'SUSPICIOUS' | 'INVALID';
  risk_reason: string | null;
}

export interface Warranty {
  registration_id: number;
  product_id: string;
  product_name: string | null;
  serial_number: string | null;
  customer_name: string;
  email: string;
  retailer: {
    retailer_id: number;
    retailer_name: string;
    city: string;
    state: string;
  } | null;
  purchase_price: number | null;
  purchase_date: string;
  warranty_status: 'ACTIVE' | 'EXPIRED' | 'VOID';
  warranty_start_date: string;
  warranty_end_date: string;
  created_at: string | null;
}

export interface DashboardStats {
  total_products: number;
  in_stock_products: number;
  sold_products: number;
  blocked_products: number;
  active_warranties: number;
  total_external_scans: number;
  suspicious_scans: number;
  invalid_scans: number;
  total_suspicious_events: number;
}

export interface VerificationResponse {
  result: 'VERIFIED' | 'SUSPICIOUS' | 'INVALID';
  explanation: string;
  risk_warnings: string[];
  scan_count: number;
  disclaimer: string;
  product: {
    product_id: string;
    product_name: string;
    serial_number: string;
    product_status: string;
    manufacturing_location: string | null;
    registration_status: string;
  } | null;
  intended_retailer: {
    retailer_id: number;
    retailer_name: string;
    address: string | null;
    city: string;
    state: string;
  } | null;
  reported_evidence: {
    reported_retailer_id: number | null;
    scan_location: string | null;
  } | null;
}

export interface RegistrationInfo {
  product_id: string;
  product_name: string;
  serial_number: string;
  manufacturing_location?: string | null;
  intended_retailer_id?: number | null;
  product_status: string;
  eligible: boolean;
}

export interface RegistrationPayload {
  customer_name: string;
  email: string;
  retailer_id: number;
  purchase_price?: number | null;
  purchase_date: string;
}

export interface RegistrationSuccessResponse {
  success: boolean;
  message: string;
  registration: {
    registration_id: number;
    customer_name: string;
    email: string;
    purchase_price: number | null;
    purchase_date: string;
    warranty_status: string;
    warranty_start_date: string;
    warranty_end_date: string;
  };
  product: {
    product_id: string;
    product_name: string;
    serial_number: string;
    product_status: string;
  };
  retailer: {
    retailer_id: number;
    retailer_name: string;
    city: string;
    state: string;
  };
}

export const api = {
  getStats: async (): Promise<DashboardStats> => {
    const res = await fetch(`${API_BASE}/api/dashboard/stats`);
    if (!res.ok) throw new Error(`Failed to load stats: ${res.statusText}`);
    return res.json();
  },

  getProducts: async (): Promise<Product[]> => {
    const res = await fetch(`${API_BASE}/api/products`);
    if (!res.ok) throw new Error(`Failed to load products: ${res.statusText}`);
    return res.json();
  },

  getProduct: async (id: string): Promise<Product> => {
    const res = await fetch(`${API_BASE}/api/products/${encodeURIComponent(id)}`);
    if (!res.ok) throw new Error(`Failed to load product ${id}: ${res.statusText}`);
    return res.json();
  },

  createProduct: async (data: {
    product_name: string;
    intended_retailer_id: number;
    serial_number?: string;
    manufacturing_location?: string;
  }): Promise<any> => {
    const res = await fetch(`${API_BASE}/api/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create product');
    }
    return res.json();
  },

  getScans: async (result?: string): Promise<ScanEvent[]> => {
    const url = result && result !== 'ALL' 
      ? `${API_BASE}/api/scans?result=${encodeURIComponent(result)}` 
      : `${API_BASE}/api/scans`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load scans: ${res.statusText}`);
    return res.json();
  },

  getWarranties: async (status?: string): Promise<Warranty[]> => {
    const url = status && status !== 'ALL'
      ? `${API_BASE}/api/warranties?status=${encodeURIComponent(status)}`
      : `${API_BASE}/api/warranties`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load warranties: ${res.statusText}`);
    return res.json();
  },

  getRetailers: async (): Promise<Retailer[]> => {
    const res = await fetch(`${API_BASE}/api/retailers`);
    if (!res.ok) throw new Error(`Failed to load retailers: ${res.statusText}`);
    return res.json();
  },

  verifyToken: async (
    token: string,
    reportedRetailerId?: number | null
  ): Promise<VerificationResponse> => {
    let url = `${API_BASE}/api/verify/${encodeURIComponent(token)}`;
    if (reportedRetailerId) {
      url += `?reported_retailer_id=${encodeURIComponent(reportedRetailerId)}`;
    }
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Verification failed: ${res.status}`);
    }
    return res.json();
  },

  getRegistrationInfo: async (token: string): Promise<RegistrationInfo> => {
    const res = await fetch(`${API_BASE}/api/register/${encodeURIComponent(token)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Registration info error: ${res.status}`);
    }
    return res.json();
  },

  registerWarranty: async (
    token: string,
    payload: RegistrationPayload
  ): Promise<RegistrationSuccessResponse> => {
    const res = await fetch(`${API_BASE}/api/register/${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Warranty registration failed');
    }
    return res.json();
  },

  getQrDownloadUrl: (productId: string, qrType: 'external' | 'internal'): string => {
    return `${API_BASE}/api/products/${encodeURIComponent(productId)}/qrs/${qrType}?download=true`;
  },

  getQrImageUrl: (productId: string, qrType: 'external' | 'internal'): string => {
    return `${API_BASE}/api/products/${encodeURIComponent(productId)}/qrs/${qrType}`;
  },
};
