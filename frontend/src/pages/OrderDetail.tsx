import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { CONTAINER_SIZE_OPTIONS, type OrderDetail } from "../types";

export default function OrderDetailPage() {
  const { id } = useParams();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api
      .order(Number(id))
      .then(setOrder)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [id]);

  if (error) {
    return (
      <div className="page">
        <div className="error-banner">{error}</div>
        <Link to="/orders">Back to orders</Link>
      </div>
    );
  }

  if (!order) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>PO {order.po_number}</h1>
          <p className="muted">
            {order.customer_name} · {order.city} · deadline {order.deadline_date}
          </p>
        </div>
        <Link className="btn" to="/orders">
          Back
        </Link>
      </div>

      <section className="card">
        <h2>Products</h2>
        {order.lines.length === 0 ? (
          <p className="muted">No standard product lines.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Bottles</th>
                <th>Cartons</th>
              </tr>
            </thead>
            <tbody>
              {order.lines.map((line) => (
                <tr key={line.id}>
                  <td>
                    {line.product_name}
                    <div className="meta">
                      {line.bottles_per_carton} bottles / carton
                    </div>
                  </td>
                  <td>{line.bottles}</td>
                  <td>{line.cartons}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Custom cartons</h2>
        {order.custom_cartons.length === 0 ? (
          <p className="muted">No custom cartons.</p>
        ) : (
          order.custom_cartons.map((carton, idx) => (
            <div key={carton.id} className="carton-block">
              <h3>
                Custom carton {idx + 1}
                {carton.label ? ` — ${carton.label}` : ""}
              </h3>
              <p className="muted">
                ×{carton.identical_count} · Outer box: {carton.outer_box_name}
              </p>
              <ul>
                {carton.items.map((item) => {
                  const sizeLabel =
                    CONTAINER_SIZE_OPTIONS.find((o) => o.value === item.container_size)
                      ?.label || item.container_size;
                  return (
                    <li key={item.id}>
                      {item.product_name} · {sizeLabel} · qty {item.qty}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
