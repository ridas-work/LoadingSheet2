import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import CustomCartonsSection, {
  emptyCarton,
} from "../components/order/CustomCartonsSection";
import OrderHeaderFields from "../components/order/OrderHeaderFields";
import ProductsSheet, {
  findSheetQtyErrors,
} from "../components/order/ProductsSheet";
import type {
  CustomCartonForm,
  Customer,
  OuterBox,
  Product,
} from "../types";

export default function OrderCreatePage() {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [sheetProducts, setSheetProducts] = useState<Product[]>([]);
  const [customProducts, setCustomProducts] = useState<Product[]>([]);
  const [outerBoxes, setOuterBoxes] = useState<OuterBox[]>([]);
  const [poNumber, setPoNumber] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [city, setCity] = useState("");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [cartons, setCartons] = useState<CustomCartonForm[]>([]);
  const [bottlesByProduct, setBottlesByProduct] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.customers(),
      api.products("sheet"),
      api.products("custom"),
      api.outerBoxes(),
    ])
      .then(([c, sheet, custom, o]) => {
        setCustomers(c);
        setSheetProducts(sheet);
        setCustomProducts(custom);
        setOuterBoxes(o);
        const initial: Record<number, string> = {};
        sheet.forEach((product) => {
          initial[product.id] = "0";
        });
        setBottlesByProduct(initial);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  function onHeaderChange(
    field: "poNumber" | "customerId" | "city" | "deadlineDate",
    value: string,
  ) {
    if (field === "poNumber") setPoNumber(value);
    if (field === "customerId") setCustomerId(value);
    if (field === "city") setCity(value);
    if (field === "deadlineDate") setDeadlineDate(value);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    const lines = Object.entries(bottlesByProduct)
      .map(([productId, bottles]) => ({
        product_id: Number(productId),
        bottles: Number(bottles),
      }))
      .filter((line) => line.bottles > 0);

    const custom_cartons = cartons.map((carton) => ({
      identical_count: Number(carton.identical_count) || 1,
      label: carton.label,
      outer_box_id: Number(carton.outer_box_id),
      items: carton.items.map((item) => ({
        product_id: Number(item.product_id),
        container_size: item.container_size,
        qty: Number(item.qty) || 1,
      })),
    }));

    if (!lines.length && !custom_cartons.length) {
      setError("Add at least one product quantity or a custom carton.");
      return;
    }

    const qtyErrors = findSheetQtyErrors(sheetProducts, bottlesByProduct);
    if (qtyErrors.length) {
      setError(qtyErrors.join(" "));
      return;
    }

    setSubmitting(true);
    try {
      const order = await api.createOrder({
        po_number: poNumber.trim(),
        customer_id: Number(customerId),
        city: city.trim(),
        deadline_date: deadlineDate,
        lines,
        custom_cartons,
      });
      navigate(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create order");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="page">Loading catalog…</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>New order</h1>
          <p className="muted">PO header, optional custom cartons, then product sheet</p>
        </div>
        <Link className="btn" to="/orders">
          Cancel
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <form className="order-form" onSubmit={onSubmit}>
        <OrderHeaderFields
          poNumber={poNumber}
          customerId={customerId}
          city={city}
          deadlineDate={deadlineDate}
          customers={customers}
          onChange={onHeaderChange}
        />

        <CustomCartonsSection
          cartons={cartons}
          products={customProducts}
          outerBoxes={outerBoxes}
          onChange={setCartons}
        />

        <ProductsSheet
          products={sheetProducts}
          bottlesByProduct={bottlesByProduct}
          onBottlesChange={(productId, bottles) =>
            setBottlesByProduct((prev) => ({ ...prev, [productId]: bottles }))
          }
        />

        <div className="form-actions">
          {cartons.length === 0 ? (
            <button
              type="button"
              className="btn"
              onClick={() => setCartons([emptyCarton()])}
            >
              Add custom carton
            </button>
          ) : null}
          <button type="submit" className="btn primary" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit order"}
          </button>
        </div>
      </form>
    </div>
  );
}
