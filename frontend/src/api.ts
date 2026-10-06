const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000/api";

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");
  return token
    ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (body) detail = JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  login(username: string, password: string) {
    return request<{
      access: string;
      refresh: string;
      user: import("./types").User;
    }>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },
  logout() {
    return request<{ detail: string }>("/auth/logout/", { method: "POST" });
  },
  me() {
    return request<import("./types").User>("/auth/me/");
  },
  customers() {
    return request<import("./types").Customer[]>("/customers/");
  },
  products(scope?: "sheet" | "custom") {
    const query = scope ? `?for=${scope}` : "";
    return request<import("./types").Product[]>(`/products/${query}`);
  },
  outerBoxes() {
    return request<import("./types").OuterBox[]>("/outer-boxes/");
  },
  orders() {
    return request<import("./types").OrderListItem[]>("/orders/");
  },
  order(id: number) {
    return request<import("./types").OrderDetail>(`/orders/${id}/`);
  },
  createOrder(payload: unknown) {
    return request<import("./types").OrderDetail>("/orders/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  marketVisitColumns() {
    return request<{
      columns: import("./types").MarketVisitColumn[];
      groups: import("./types").MarketVisitColumnGroup[];
    }>("/market-visits/columns/");
  },
  marketVisits(status?: "in_process" | "submitted") {
    const query = status ? `?status=${status}` : "";
    return request<import("./types").MarketVisitListItem[]>(
      `/market-visits/${query}`,
    );
  },
  marketVisit(id: number) {
    return request<import("./types").MarketVisitDetail>(`/market-visits/${id}/`);
  },
  createMarketVisit(payload: {
    visit_date: string;
    action: "save" | "submit";
    stores: unknown[];
  }) {
    return request<
      import("./types").MarketVisitDetail | { deleted: boolean; detail: string }
    >("/market-visits/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateMarketVisit(
    id: number,
    payload: {
      visit_date: string;
      action: "save" | "submit";
      stores: unknown[];
    },
  ) {
    return request<
      import("./types").MarketVisitDetail | { deleted: boolean; detail: string }
    >(`/market-visits/${id}/`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  deleteMarketVisit(id: number) {
    return request<void>(`/market-visits/${id}/`, { method: "DELETE" });
  },
  batchProducts() {
    return request<import("./types").BatchProduct[]>("/batch-products/");
  },
  batches(params?: { purpose?: string; search?: string; status?: string }) {
    const q = new URLSearchParams();
    q.set("status", params?.status || "active");
    if (params?.purpose) q.set("purpose", params.purpose);
    if (params?.search) q.set("search", params.search);
    return request<import("./types").Batch[]>(`/batches/?${q.toString()}`);
  },
  batch(id: number) {
    return request<import("./types").Batch>(`/batches/${id}/`);
  },
  createBatch(payload: unknown) {
    return request<import("./types").Batch>("/batches/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateBatch(id: number, payload: unknown) {
    return request<import("./types").Batch>(`/batches/${id}/`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
  deleteBatch(id: number) {
    return request<void>(`/batches/${id}/`, { method: "DELETE" });
  },
  packagingMaterials(params?: { search?: string }) {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    const qs = q.toString();
    return request<import("./types").PackagingMaterial[]>(
      `/packaging-materials/${qs ? `?${qs}` : ""}`,
    );
  },
  createPackagingMaterial(payload: {
    name: string;
    material_type?: string;
    purchased_qty?: number;
    rejected_qty?: number;
  }) {
    return request<import("./types").PackagingMaterial>(
      "/packaging-materials/",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },
  updatePackagingMaterial(
    id: number,
    payload: {
      name?: string;
      code?: string;
      purchased_qty?: number;
      rejected_qty?: number;
      material_type?: string;
    },
  ) {
    return request<import("./types").PackagingMaterial>(
      `/packaging-materials/${id}/`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
    );
  },
};
