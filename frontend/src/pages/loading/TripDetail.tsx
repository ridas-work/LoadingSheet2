import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { LoadingTrip } from "../../types";

export default function LoadingTripDetailPage() {
  const { user } = useAuth();
  const { id } = useParams();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<LoadingTrip | null>(null);
  const [loading, setLoading] = useState(true);
  const [delivering, setDelivering] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (user?.role !== "loading_clerk" && user?.role !== "admin") return;
    if (!id) return;
    api
      .loadingTrip(Number(id))
      .then(setTrip)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user, id]);

  if (user && user.role !== "loading_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  async function markDelivered() {
    if (!trip) return;
    const ok = window.confirm(
      `Mark trip ${trip.vehicle_no} as delivered?\n\nThis deducts Ready stock on-hand and Esha liters for lines assigned directly from Esha. This cannot be undone.`,
    );
    if (!ok) return;
    setDelivering(true);
    setError("");
    setNote("");
    try {
      await api.deliverLoadingTrip(trip.id);
      setNote("Trip marked delivered. Stock deducted.");
      setTimeout(() => navigate("/loading"), 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deliver failed");
    } finally {
      setDelivering(false);
    }
  }

  return (
    <div className="page loading-page">
      <div className="page-header">
        <div>
          <h1>Dispatch trip</h1>
          <p className="muted">
            Vehicle {trip?.vehicle_no || "—"} · {trip?.order_count ?? 0} PO
            {(trip?.order_count ?? 0) === 1 ? "" : "s"} ·{" "}
            {trip?.assigned_lines ?? 0}/{trip?.total_lines ?? 0} batches assigned
          </p>
        </div>
        <div className="row-actions">
          <button
            type="button"
            className="btn primary"
            onClick={markDelivered}
            disabled={!trip || delivering || loading}
          >
            {delivering ? "Delivering…" : "Mark delivered"}
          </button>
          <Link className="btn" to="/loading">
            Back to trips
          </Link>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {note ? <div className="success-banner">{note}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {trip ? (
        <>
          <section className="card">
            <div className="page-header" style={{ marginBottom: "0.75rem" }}>
              <div>
                <h2>Loading sheets</h2>
                <p className="muted">
                  Assign Ready stock or Esha batches and carton weights. Save
                  progress anytime. Deduction happens when you mark delivered.
                </p>
              </div>
              <div className="row-actions">
                <Link
                  className="btn primary"
                  to={`/loading/trips/${trip.id}/sheet`}
                >
                  Combined loading sheet
                </Link>
              </div>
            </div>

            <div className="dispatch-order-list">
              {(trip.trip_orders || []).map((o) => (
                <div key={o.order_id} className="dispatch-order-card">
                  <div className="dispatch-order-main">
                    <div className="dispatch-order-po">
                      {o.po_number} — {o.customer_name}
                    </div>
                    <div className="muted">
                      {o.assigned_lines}/{o.total_lines} batches assigned
                      {o.challan_no ? ` · DC ${o.challan_no}` : ""}
                    </div>
                  </div>
                  <Link
                    className="btn"
                    to={`/loading/trips/${trip.id}/sheet?order_id=${o.order_id}`}
                  >
                    Assign batches
                  </Link>
                </div>
              ))}
            </div>
          </section>

          <section className="card">
            <h2>Trip details</h2>
            <div className="row-2">
              <div>
                <div className="muted">Vehicle</div>
                <div>{trip.vehicle_no || "—"}</div>
              </div>
              <div>
                <div className="muted">Driver</div>
                <div>{trip.driver_name || "—"}</div>
              </div>
              <div>
                <div className="muted">Default challan / DC</div>
                <div>{trip.default_challan_no || "—"}</div>
              </div>
              <div>
                <div className="muted">Helper</div>
                <div>{trip.helper_name || "—"}</div>
              </div>
              <div>
                <div className="muted">Production incharge</div>
                <div>{trip.production_incharge || "—"}</div>
              </div>
              <div>
                <div className="muted">Security</div>
                <div>{trip.security || "—"}</div>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
