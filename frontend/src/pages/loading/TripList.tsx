import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { LoadingTrip } from "../../types";

export default function LoadingTripListPage() {
  const { user } = useAuth();
  const [trips, setTrips] = useState<LoadingTrip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role !== "loading_clerk" && user?.role !== "admin") return;
    api
      .loadingTrips()
      .then(setTrips)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  if (user && user.role !== "loading_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page loading-page">
      <div className="page-header">
        <div>
          <h1>Dispatch &amp; ready stock</h1>
          <p className="muted">
            Assign batches, record filling, and ship from factory-ready inventory.
          </p>
        </div>
      </div>

      <section className="dispatch-section">
        <h2>Dispatch trips</h2>
        <p className="muted">
          Pending batch-assignment trips only — delivered trips are hidden.
        </p>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading && trips.length === 0 ? (
        <div className="empty-state">
          <p>No planned trips waiting for batch assignment.</p>
        </div>
      ) : null}

      <div className="dispatch-order-list">
        {trips.map((t) => (
          <div key={t.id} className="dispatch-order-card loading-trip-card">
            <div className="dispatch-order-main">
              <div className="dispatch-order-po">
                Vehicle {t.vehicle_no || "—"}
              </div>
              <div className="dispatch-order-customer">
                {t.order_count} PO{t.order_count === 1 ? "" : "s"}
                {t.po_numbers.length
                  ? `: ${t.po_numbers.join(", ")}`
                  : ""}
              </div>
              <div className="muted">
                Updated {new Date(t.updated_at).toLocaleString()} ·{" "}
                {t.assigned_lines}/{t.total_lines} batches assigned
              </div>
            </div>
            <Link className="btn primary" to={`/loading/trips/${t.id}`}>
              Open trip
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
