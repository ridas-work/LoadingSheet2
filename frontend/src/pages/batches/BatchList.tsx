import { useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { Batch, BatchPurpose } from "../../types";

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function formatQty(qty: string, unit: string) {
  const n = Number(qty);
  if (Number.isInteger(n)) return `${n} ${unit}`;
  return `${qty} ${unit}`;
}

function formatRemaining(liters: string) {
  const n = Number(liters);
  if (Number.isInteger(n)) return `${n} L`;
  return `${liters} L`;
}

export default function BatchListPage() {
  const { user } = useAuth();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [purpose, setPurpose] = useState<"all" | BatchPurpose>("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.batches({
        status: "active",
        purpose: purpose === "all" ? undefined : purpose,
        search: search.trim() || undefined,
      });
      setBatches(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user?.role !== "batch_clerk" && user?.role !== "admin") return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, purpose]);

  const filteredNote = useMemo(
    () => `${batches.length} batch${batches.length === 1 ? "" : "es"}`,
    [batches.length],
  );

  if (user && user.role !== "batch_clerk" && user.role !== "admin") {
    return <Navigate to="/orders" replace />;
  }

  async function onDelete(id: number, batchNo: string) {
    if (!window.confirm(`Delete batch ${batchNo}?`)) return;
    try {
      await api.deleteBatch(id);
      setBatches((prev) => prev.filter((b) => b.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="page batch-page">
      <div className="page-header">
        <div>
          <h1>Active batches</h1>
          <div className="filter-tabs">
            <button type="button" className="filter-tab active">
              Active batches
            </button>
            <span className="filter-tab disabled">Closed batches</span>
            <span className="filter-tab disabled">Where it went</span>
          </div>
          <div className="filter-tabs">
            {(
              [
                ["all", "All"],
                ["regular", "Regular production"],
                ["sample", "Sample production"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`filter-tab${purpose === value ? " active" : ""}`}
                onClick={() => setPurpose(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="muted">{loading ? "Loading…" : filteredNote}</p>
        </div>
        <Link className="btn primary pill-btn" to="/batches/new">
          New batch
        </Link>
      </div>

      <div className="batch-toolbar">
        <input
          className="search-input"
          placeholder="Search batch no or product..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") load();
          }}
        />
        <button type="button" className="btn" onClick={load}>
          Search
        </button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="card table-wrap">
        <table className="batch-table">
          <thead>
            <tr>
              <th>Batch no</th>
              <th>Product</th>
              <th>Purpose</th>
              <th>Date</th>
              <th>Status</th>
              <th>pH</th>
              <th>Quantity</th>
              <th>Remaining</th>
              <th>By</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {!loading && batches.length === 0 ? (
              <tr>
                <td colSpan={10} className="muted">
                  No active batches yet.
                </td>
              </tr>
            ) : null}
            {batches.map((b) => (
              <tr key={b.id}>
                <td>
                  <Link to={`/batches/${b.id}`}>{b.batch_number}</Link>
                </td>
                <td>{b.batch_product_name}</td>
                <td>
                  <span
                    className={`tag ${
                      b.purpose === "sample" ? "tag-sample" : "tag-regular"
                    }`}
                  >
                    {b.purpose === "sample" ? "Sample" : "Regular"}
                  </span>
                </td>
                <td>{formatDate(b.date)}</td>
                <td>
                  <span
                    className={`tag ${
                      b.qc_result === "unsuccessful"
                        ? "tag-bad"
                        : "tag-available"
                    }`}
                  >
                    {b.status_label}
                  </span>
                </td>
                <td>{b.ph || "—"}</td>
                <td>{formatQty(b.quantity, b.quantity_unit)}</td>
                <td>{formatRemaining(b.remaining_quantity)}</td>
                <td>{b.created_by_name}</td>
                <td className="row-actions">
                  <Link className="btn" to={`/batches/${b.id}`}>
                    Edit
                  </Link>
                  <button
                    type="button"
                    className="btn danger"
                    onClick={() => onDelete(b.id, b.batch_number)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
