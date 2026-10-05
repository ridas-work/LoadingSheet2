import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { OrderListItem } from "../types";

export default function OrdersListPage() {
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .orders()
      .then(setOrders)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>My orders</h1>
          <p className="muted">Orders you have submitted</p>
        </div>
        <Link className="btn primary" to="/orders/new">
          New order
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p>Loading…</p> : null}

      {!loading && orders.length === 0 ? (
        <div className="empty-state">
          <p>No orders yet.</p>
          <Link className="btn primary" to="/orders/new">
            Create first order
          </Link>
        </div>
      ) : null}

      {orders.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>PO</th>
                <th>Customer</th>
                <th>City</th>
                <th>Deadline</th>
                <th>Products</th>
                <th>Bottles</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>
                    <Link to={`/orders/${o.id}`}>{o.po_number}</Link>
                  </td>
                  <td>{o.customer_name}</td>
                  <td>{o.city}</td>
                  <td>{o.deadline_date}</td>
                  <td>{o.total_products}</td>
                  <td>{o.total_bottles}</td>
                  <td>{new Date(o.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
