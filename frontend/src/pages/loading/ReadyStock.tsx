import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type {
  ReadyStockBatchOption,
  ReadyStockFormComponent,
  ReadyStockFormProduct,
  ReadyStockLot,
} from "../../types";

const OTHER = "__other__";

type CompPick = { mode: string; label: string };

function BatchPicker({
  label,
  batches,
  mode,
  freeText,
  onMode,
  onFreeText,
  required,
}: {
  label: string;
  batches: ReadyStockBatchOption[];
  mode: string;
  freeText: string;
  onMode: (v: string) => void;
  onFreeText: (v: string) => void;
  required?: boolean;
}) {
  return (
    <div className="ready-batch-picker">
      <label>
        {label}
        <select
          value={mode}
          onChange={(e) => onMode(e.target.value)}
          required={required}
        >
          <option value="">Select batch…</option>
          {batches.map((b) => (
            <option key={b.id} value={String(b.id)}>
              {b.batch_number} — {Number(b.remaining_quantity)} L left
            </option>
          ))}
          <option value={OTHER}>Other (not in Esha)</option>
        </select>
      </label>
      {mode === OTHER ? (
        <label>
          Batch label
          <input
            value={freeText}
            onChange={(e) => onFreeText(e.target.value)}
            placeholder="e.g. OLD-B-99"
            required
          />
        </label>
      ) : null}
    </div>
  );
}

export default function ReadyStockPage() {
  const { user } = useAuth();
  const [lots, setLots] = useState<ReadyStockLot[]>([]);
  const [totalBottles, setTotalBottles] = useState(0);
  const [products, setProducts] = useState<ReadyStockFormProduct[]>([]);
  const [productId, setProductId] = useState("");
  const [batchMode, setBatchMode] = useState("");
  const [batchLabel, setBatchLabel] = useState("");
  const [bottles, setBottles] = useState("");
  const [sets, setSets] = useState("");
  const [compPicks, setCompPicks] = useState<Record<number, CompPick>>({});
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [note, setNote] = useState("");

  const selected = useMemo(
    () => products.find((p) => String(p.id) === productId) || null,
    [products, productId],
  );

  async function reloadMetaAndStock(search = filter) {
    const [meta, stock] = await Promise.all([
      api.readyStockFormMeta(),
      api.readyStock(search.trim() || undefined),
    ]);
    setProducts(meta.products);
    setLots(stock.lots);
    setTotalBottles(stock.total_bottles);
  }

  async function load(search = filter) {
    const data = await api.readyStock(search.trim() || undefined);
    setLots(data.lots);
    setTotalBottles(data.total_bottles);
  }

  useEffect(() => {
    if (user?.role !== "loading_clerk" && user?.role !== "admin") return;
    reloadMetaAndStock()
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  if (user && user.role !== "loading_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  const deductHint = useMemo(() => {
    if (!selected) return "";
    if (selected.is_bundle) {
      const n = Number(sets);
      if (!Number.isFinite(n) || n < 1) return "";
      const parts: string[] = [];
      for (const c of selected.components) {
        const pick = compPicks[c.product_id];
        if (!pick || pick.mode === "" || pick.mode === OTHER) continue;
        if (!c.fill_volume_liters) continue;
        const liters = n * c.qty_per_set * Number(c.fill_volume_liters);
        parts.push(`${liters.toFixed(3)} L from ${c.product_name}`);
      }
      return parts.length ? `Will deduct: ${parts.join("; ")}` : "";
    }
    const n = Number(bottles);
    if (
      !Number.isFinite(n) ||
      n < 1 ||
      !selected.fill_volume_liters ||
      !batchMode ||
      batchMode === OTHER
    ) {
      return "";
    }
    const liters = n * Number(selected.fill_volume_liters);
    return `Will deduct ${liters.toFixed(3)} L from the selected Esha batch.`;
  }, [selected, sets, bottles, batchMode, compPicks]);

  function setCompMode(c: ReadyStockFormComponent, mode: string) {
    setCompPicks((prev) => ({
      ...prev,
      [c.product_id]: { mode, label: prev[c.product_id]?.label || "" },
    }));
  }

  function setCompLabel(c: ReadyStockFormComponent, label: string) {
    setCompPicks((prev) => ({
      ...prev,
      [c.product_id]: {
        mode: prev[c.product_id]?.mode || OTHER,
        label,
      },
    }));
  }

  async function onAdd(e: FormEvent) {
    e.preventDefault();
    if (!selected) {
      setError("Select a product.");
      return;
    }
    setSaving(true);
    setError("");
    setNote("");
    try {
      if (selected.is_bundle) {
        const components = selected.components.map((c) => {
          const pick = compPicks[c.product_id] || { mode: "", label: "" };
          if (!pick.mode) throw new Error(`Select a batch for ${c.product_name}.`);
          if (pick.mode === OTHER) {
            const label = pick.label.trim();
            if (!label) throw new Error(`Enter batch label for ${c.product_name}.`);
            return { product_id: c.product_id, batch_label: label };
          }
          return { product_id: c.product_id, batch_id: Number(pick.mode) };
        });
        await api.addReadyStock({
          product_id: selected.id,
          sets: Number(sets),
          components,
        });
      } else {
        if (!batchMode) throw new Error("Select a batch.");
        if (batchMode === OTHER) {
          await api.addReadyStock({
            product_id: selected.id,
            batch_label: batchLabel.trim(),
            bottles: Number(bottles),
          });
        } else {
          await api.addReadyStock({
            product_id: selected.id,
            batch_id: Number(batchMode),
            bottles: Number(bottles),
          });
        }
      }
      setBatchMode("");
      setBatchLabel("");
      setBottles("");
      setSets("");
      setCompPicks({});
      setNote("Ready stock added.");
      await reloadMetaAndStock();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Add failed");
    } finally {
      setSaving(false);
    }
  }

  async function onEdit(lot: ReadyStockLot) {
    const unit = lot.unit_label || (lot.is_bundle ? "sets" : "bottles");
    const next = window.prompt(
      `On hand (${unit}) for ${lot.product_name} / ${lot.batch_label}`,
      String(lot.on_hand),
    );
    if (next == null) return;
    const n = Number(next);
    if (!Number.isInteger(n) || n < 0) {
      setError("On hand must be a non-negative whole number.");
      return;
    }
    setError("");
    try {
      await api.patchReadyStock(lot.id, { on_hand: n });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  return (
    <div className="page loading-page pending-orders-page">
      <div className="page-header">
        <div>
          <h1>Ready stock</h1>
          <p className="muted">
            Fill from an active Esha batch (liters deduct now) or enter a
            free-text batch not in QC. Bundles stay as sealed sets.
          </p>
        </div>
      </div>

      <div className="info-banner ready-stock-banner">
        <div>
          Pick an <strong>Esha batch</strong> to deduct liters when filling, or{" "}
          <strong>Other</strong> for old stock with no QC batch.{" "}
          <strong>Left to assign</strong> = on hand minus bottles already on
          planned sheets; physical on-hand drops only when a trip is delivered.
        </div>
        <div className="ready-stock-total">{totalBottles} on hand total</div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {note ? <div className="success-banner">{note}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      <form className="card ready-stock-form" onSubmit={onAdd}>
        <h2>Add ready stock</h2>
        <label>
          Product
          <select
            value={productId}
            onChange={(e) => {
              setProductId(e.target.value);
              setBatchMode("");
              setBatchLabel("");
              setCompPicks({});
            }}
            required
          >
            <option value="">Select…</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>

        {selected?.is_bundle ? (
          <>
            <div className="info-banner">
              <strong>Sealed sets:</strong> pick a batch per component, then how
              many complete sets are on the shelf. Recorded as{" "}
              <strong>{selected.name}</strong>.
            </div>
            {selected.components.map((c) => {
              const pick = compPicks[c.product_id] || { mode: "", label: "" };
              return (
                <BatchPicker
                  key={c.product_id}
                  label={`Batch — ${c.product_name}`}
                  batches={c.available_batches || []}
                  mode={pick.mode}
                  freeText={pick.label}
                  onMode={(v) => setCompMode(c, v)}
                  onFreeText={(v) => setCompLabel(c, v)}
                  required
                />
              );
            })}
            <label>
              Complete sealed sets on shelf
              <input
                type="number"
                min={1}
                step={1}
                value={sets}
                onChange={(e) => setSets(e.target.value)}
                placeholder="e.g. 50"
                required
              />
            </label>
          </>
        ) : selected ? (
          <>
            <BatchPicker
              label="Batch"
              batches={selected.available_batches || []}
              mode={batchMode}
              freeText={batchLabel}
              onMode={setBatchMode}
              onFreeText={setBatchLabel}
              required
            />
            <label>
              Bottles already filled
              <input
                type="number"
                min={1}
                step={1}
                value={bottles}
                onChange={(e) => setBottles(e.target.value)}
                placeholder="e.g. 200"
                required
              />
            </label>
          </>
        ) : null}

        {deductHint ? <p className="help">{deductHint}</p> : null}

        <div className="form-actions">
          <button type="submit" className="btn primary" disabled={saving}>
            {saving ? "Adding…" : "Add ready stock"}
          </button>
        </div>
      </form>

      <section className="card">
        <div className="page-header" style={{ marginBottom: "0.75rem" }}>
          <h2>On hand by batch</h2>
          <div className="batch-toolbar" style={{ marginBottom: 0 }}>
            <input
              className="search-input"
              placeholder="Filter by product or batch"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") load();
              }}
            />
            <button type="button" className="btn" onClick={() => load()}>
              Search
            </button>
          </div>
        </div>
        <div className="table-wrap">
          <table className="batch-table pending-orders-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Batch no.</th>
                <th>On hand</th>
                <th>Left to assign</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {lots.length === 0 ? (
                <tr>
                  <td colSpan={5} className="muted">
                    No ready stock yet.
                  </td>
                </tr>
              ) : null}
              {lots.map((lot) => {
                const unit =
                  lot.unit_label || (lot.is_bundle ? "sets" : "bottles");
                const left =
                  lot.available_to_assign != null
                    ? lot.available_to_assign
                    : lot.on_hand;
                const assigned = lot.assigned_bottles ?? 0;
                return (
                  <tr
                    key={lot.id}
                    className={left <= 0 && lot.on_hand > 0 ? "row-invalid" : undefined}
                  >
                    <td>{lot.product_name}</td>
                    <td className="pending-po">{lot.batch_label}</td>
                    <td>
                      {lot.on_hand} <span className="muted">{unit}</span>
                    </td>
                    <td>
                      {left} <span className="muted">{unit}</span>
                      {assigned > 0 ? (
                        <div className="muted" style={{ fontSize: "0.85rem" }}>
                          {assigned} assigned on planned trips
                        </div>
                      ) : null}
                    </td>
                    <td className="row-actions">
                      <button
                        type="button"
                        className="btn"
                        onClick={() => onEdit(lot)}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
