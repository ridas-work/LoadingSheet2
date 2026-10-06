import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { DispatchOrder } from "../../types";

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function DispatchOrdersPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<DispatchOrder[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role !== "dispatch_clerk" && user?.role !== "admin") return;
    api
      .dispatchOrders()
      .then(setOrders)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  const selectedSet = useMemo(() => new Set(selected), [selected]);

  if (user && user.role !== "dispatch_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  function toggle(id: number) {
    setError("");
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  function startTrip() {
    if (selected.length === 0) {
      setError("Select at least one PO (checkbox), then click Create trip.");
      return;
    }
    const ids = selected.join(",");
    navigate(`/dispatch/trips/new?orders=${ids}`);
  }

  return (
    <div className="page dispatch-page">
      <div className="page-header">
        <div>
          <h1>Dispatch trips &amp; orders</h1>
          <p className="muted">
            Plan vehicle trips, pick POs, and build loading sheets for the gate.
          </p>
        </div>
        <button type="button" className="btn primary" onClick={startTrip}>
          Create trip ({selected.length})
        </button>
      </div>

      <section className="dispatch-section">
        <h2>Orders</h2>
        <p className="muted">
          Tick one or more POs below, then press Create trip.
        </p>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading && orders.length === 0 ? (
        <div className="empty-state">
          <p>No pending orders for dispatch.</p>
        </div>
      ) : null}

      <div className="dispatch-order-list">
        {orders.map((o) => {
          const checked = selectedSet.has(o.id);
          return (
            <div
              key={o.id}
              role="button"
              tabIndex={0}
              className={`dispatch-order-card${checked ? " selected" : ""}`}
              onClick={() => toggle(o.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  toggle(o.id);
                }
              }}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggle(o.id)}
                onClick={(e) => e.stopPropagation()}
              />
              <div className="dispatch-order-main">
                <div className="dispatch-order-po">{o.po_number}</div>
                <div className="dispatch-order-customer">{o.customer_name}</div>
                <div className="muted">
                  {formatDate(o.deadline_date)} · {o.city} · by{" "}
                  {o.created_by_username}
                </div>
              </div>
              <div className="dispatch-order-meta muted">
                {o.total_products} products · {o.total_bottles || 0} bottles
              </div>
            </div>
          );
        })}
      </div>

      {selected.length > 0 ? (
        <div className="form-actions sticky-actions">
          <p className="muted">Select POs below to start a multi-PO trip.</p>
          <button type="button" className="btn primary" onClick={startTrip}>
            Create trip with {selected.length} PO
            {selected.length === 1 ? "" : "s"}
          </button>
          <Link className="btn" to="/dispatch/trips">
            View trips
          </Link>
        </div>
      ) : null}
    </div>
  );
}
