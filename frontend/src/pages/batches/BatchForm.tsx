import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type {
  BatchProduct,
  BatchPurpose,
  BatchQCResult,
  BatchQuantityUnit,
} from "../../types";

function todayISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function BatchFormPage() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const { user } = useAuth();

  const [products, setProducts] = useState<BatchProduct[]>([]);
  const [purpose, setPurpose] = useState<BatchPurpose>("regular");
  const [batchNumber, setBatchNumber] = useState("");
  const [productId, setProductId] = useState("");
  const [date, setDate] = useState(todayISO());
  const [ph, setPh] = useState("");
  const [solids, setSolids] = useState("");
  const [appearance, setAppearance] = useState("");
  const [provider, setProvider] = useState("");
  const [quantity, setQuantity] = useState("");
  const [quantityUnit, setQuantityUnit] = useState<BatchQuantityUnit>("L");
  const [customerName, setCustomerName] = useState("");
  const [qcResult, setQcResult] = useState<BatchQCResult>("successful");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.role !== "batch_clerk" && user?.role !== "admin") return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const list = await api.batchProducts();
        if (cancelled) return;
        setProducts(list);
        if (isNew) {
          setDate(todayISO());
        } else {
          const batch = await api.batch(Number(id));
          if (cancelled) return;
          setPurpose(batch.purpose);
          setBatchNumber(batch.batch_number);
          setProductId(String(batch.batch_product_id));
          setDate(batch.date);
          setPh(batch.ph || "");
          setSolids(batch.solids || "");
          setAppearance(batch.appearance || "");
          setProvider(batch.provider || "");
          setQuantity(String(batch.quantity));
          setQuantityUnit(batch.quantity_unit);
          setCustomerName(batch.customer_name || "");
          setQcResult(batch.qc_result);
          setComment(batch.comment || "");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, id, isNew]);

  if (user && user.role !== "batch_clerk" && user.role !== "admin") {
    return <Navigate to="/orders" replace />;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    const payload = {
      purpose,
      batch_number: batchNumber.trim(),
      batch_product_id: Number(productId),
      date,
      ph: ph.trim(),
      solids: solids.trim(),
      appearance: appearance.trim(),
      provider: provider.trim(),
      quantity,
      quantity_unit: quantityUnit,
      customer_name: customerName.trim(),
      qc_result: qcResult,
      comment: comment.trim(),
    };
    try {
      if (isNew) {
        await api.createBatch(payload);
      } else {
        await api.updateBatch(Number(id), payload);
      }
      navigate("/batches");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page batch-form-page">
      <div className="page-header">
        <div>
          <h1>{isNew ? "New batch" : `Edit batch ${batchNumber}`}</h1>
          <p className="muted">
            Enter production batches for filling. Parent product only — sizes come
            later when assigning.
          </p>
        </div>
        <Link className="btn" to="/batches">
          Back
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p>Loading…</p> : null}

      {!loading ? (
        <form className="card batch-form" onSubmit={onSubmit}>
          <div className="purpose-toggle">
            <button
              type="button"
              className={purpose === "regular" ? "active" : ""}
              onClick={() => setPurpose("regular")}
            >
              Regular production
            </button>
            <button
              type="button"
              className={purpose === "sample" ? "active" : ""}
              onClick={() => setPurpose("sample")}
            >
              Sample production
            </button>
          </div>
          <p className="help">
            {purpose === "regular"
              ? "Regular tag is for Esha's filters. Rashid can assign this batch on POs, trips, or sample orders."
              : "Sample batches are tracked separately and can still be assigned later when successful."}
          </p>

          <label>
            Batch number
            <input
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              placeholder="e.g. 250728-1"
              required
            />
          </label>

          <label>
            Product
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              required
            >
              <option value="">Select product...</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <span className="help">
              Rhino, Brighten, Fabrito, Degrease, Glim, Titan, and Washout
              (Lemon / Floral / Ocean) — parent products only.
            </span>
          </label>

          <label>
            Date
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </label>

          <label>
            pH
            <input
              value={ph}
              onChange={(e) => setPh(e.target.value)}
              placeholder="e.g. 7 or 6.5-7"
            />
          </label>

          <label>
            Solids
            <input
              value={solids}
              onChange={(e) => setSolids(e.target.value)}
              placeholder="e.g. 29-30% (sinking 17)"
            />
          </label>

          <label>
            Appearance
            <input
              value={appearance}
              onChange={(e) => setAppearance(e.target.value)}
              placeholder="e.g. Clear liquid"
            />
          </label>

          <label>
            Provider
            <input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="e.g. Ramzan"
            />
          </label>

          <label>
            Quantity
            <div className="qty-row">
              <input
                type="number"
                min={0}
                step="any"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="e.g. 350"
                required
              />
              <div className="unit-toggle">
                <button
                  type="button"
                  className={quantityUnit === "L" ? "active" : ""}
                  onClick={() => setQuantityUnit("L")}
                >
                  L
                </button>
                <button
                  type="button"
                  className={quantityUnit === "ml" ? "active" : ""}
                  onClick={() => setQuantityUnit("ml")}
                >
                  ml
                </button>
              </div>
            </div>
            <span className="help">
              Use liters for full batches, or ml for small/sample amounts (1000 ml
              = 1 L).
            </span>
          </label>

          <label>
            Customer (optional)
            <input
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="Customer name if known"
            />
          </label>

          <div className="qc-box">
            <h3>QC result</h3>
            <p className="help">
              Was this batch prepared successfully? Unsuccessful batches stay in
              the list but are not available for dispatch until corrected and
              marked successful.
            </p>
            <div className="qc-toggle">
              <button
                type="button"
                className={qcResult === "successful" ? "active" : ""}
                onClick={() => setQcResult("successful")}
              >
                Successful
              </button>
              <button
                type="button"
                className={`bad ${qcResult === "unsuccessful" ? "active" : ""}`}
                onClick={() => setQcResult("unsuccessful")}
              >
                Unsuccessful
              </button>
            </div>
            <label>
              Comment (optional)
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Any notes about this batch preparation..."
              />
            </label>
          </div>

          <p className="help">
            Stored as entered. Also used for dispatch remaining-volume checks.
          </p>

          <button type="submit" className="btn primary block" disabled={saving}>
            {saving ? "Saving…" : "Save batch"}
          </button>
        </form>
      ) : null}
    </div>
  );
}
