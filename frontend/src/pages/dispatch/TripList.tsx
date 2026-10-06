import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { Trip } from "../../types";

export default function TripListPage() {
  const { user } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role !== "dispatch_clerk" && user?.role !== "admin") return;
    api
      .trips()
      .then(setTrips)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  if (user && user.role !== "dispatch_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page dispatch-page">
      <div className="page-header">
        <div>
          <h1>Dispatch trips</h1>
          <p className="muted">Vehicle trips you can edit until delivery (later).</p>
        </div>
        <Link className="btn primary" to="/dispatch">
          Orders pool
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading && trips.length === 0 ? (
        <div className="empty-state">
          <p>No trips yet.</p>
          <Link className="btn primary" to="/dispatch">
            Select orders
          </Link>
        </div>
      ) : null}

      {trips.length > 0 ? (
        <div className="table-wrap card">
          <table className="batch-table">
            <thead>
              <tr>
                <th>Trip</th>
                <th>Vehicle</th>
                <th>Driver</th>
                <th>Default challan</th>
                <th>POs</th>
                <th>Status</th>
                <th>By</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {trips.map((t) => (
                <tr key={t.id}>
                  <td>#{t.id}</td>
                  <td>{t.vehicle_no || "—"}</td>
                  <td>{t.driver_name || "—"}</td>
                  <td>{t.default_challan_no || "—"}</td>
                  <td>{t.order_count}</td>
                  <td>
                    <span className="tag tag-regular">{t.status}</span>
                  </td>
                  <td>{t.created_by_name}</td>
                  <td className="row-actions">
                    <Link className="btn" to={`/dispatch/trips/${t.id}`}>
                      Edit
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
