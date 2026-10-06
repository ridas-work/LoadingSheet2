import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { LoadingPendingOrder } from "../../types";

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function PendingOrdersPage() {
  const { user } = useAuth();
  const [orders, setOrders] = useState<LoadingPendingOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role !== "loading_clerk" && user?.role !== "admin") return;
    api
      .loadingPendingOrders()
      .then(setOrders)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  if (user && user.role !== "loading_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="page loading-page pending-orders-page">
      <div className="page-header">
        <div>
          <h1>Pending POs</h1>
          <p className="muted">
            All orders still to deliver — whether already on a trip or waiting
            for Ali to assign one.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading && orders.length === 0 ? (
        <div className="empty-state">
          <p>No pending orders.</p>
        </div>
      ) : null}

      {orders.length > 0 ? (
        <div className="table-wrap card pending-orders-table-wrap">
          <table className="batch-table pending-orders-table">
            <thead>
              <tr>
                <th>PO</th>
                <th>Customer</th>
                <th>City</th>
                <th>Deadline</th>
                <th>Entered by</th>
                <th>Products</th>
                <th>Trip</th>
                <th>Challan / DC</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td className="pending-po">{o.po_number}</td>
                  <td>{o.customer_name}</td>
                  <td>{o.city}</td>
                  <td className="pending-nowrap">{formatDate(o.deadline_date)}</td>
                  <td>{o.created_by_username}</td>
                  <td className="pending-nowrap">
                    {o.total_products} · {o.total_bottles || 0} bottles
                  </td>
                  <td>
                    {o.on_trip ? (
                      <span className="tag tag-available">
                        Trip #{o.trip_id}
                        {o.trip_vehicle_no ? ` · ${o.trip_vehicle_no}` : ""}
                      </span>
                    ) : (
                      <span className="tag tag-regular">Not on trip</span>
                    )}
                  </td>
                  <td>{o.challan_no || "—"}</td>
                  <td className="row-actions">
                    {o.on_trip && o.trip_id ? (
                      <Link className="btn" to={`/loading/trips/${o.trip_id}`}>
                        Open trip
                      </Link>
                    ) : (
                      <span className="muted">Waiting for dispatch</span>
                    )}
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
