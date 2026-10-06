import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type {
  LoadingSheetLine,
  ReadyStockBatchOption,
  ReadyStockLot,
} from "../../types";

type Draft = {
  /** "lot:123" | "batch:45" | "" */
  assignment: string;
  carton_weight_kg: string;
};

function weightWarning(
  boxLines: LoadingSheetLine[],
  entered: string,
): string | null {
  if (boxLines.length !== 1) return null;
  const line = boxLines[0];
  if (line.standard_weight_kg == null) return null;
  if (line.bottles !== line.bottles_per_carton) return null;
  const value = Number(entered);
  if (entered.trim() === "" || !Number.isFinite(value)) return null;
  const std = Number(line.standard_weight_kg);
  const pct = line.weight_tolerance_pct || 8;
  const lo = std * (1 - pct / 100);
  const hi = std * (1 + pct / 100);
  if (value >= lo && value <= hi) return null;
  return `Weight ${value} kg is outside standard ${std} kg (±${pct}%). Check the box — bottles missing or extra?`;
}

function assignmentFromLine(line: LoadingSheetLine): string {
  if (line.ready_stock_lot_id != null) return `lot:${line.ready_stock_lot_id}`;
  if (line.source_batch_id != null) return `batch:${line.source_batch_id}`;
  return "";
}

export default function LoadingSheetPage() {
  const { user } = useAuth();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const orderIdParam = searchParams.get("order_id");
  const orderId = orderIdParam ? Number(orderIdParam) : undefined;

  const [lines, setLines] = useState<LoadingSheetLine[]>([]);
  const [lots, setLots] = useState<ReadyStockLot[]>([]);
  const [batches, setBatches] = useState<ReadyStockBatchOption[]>([]);
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [vehicleNo, setVehicleNo] = useState("");
  const [driverName, setDriverName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedNote, setSavedNote] = useState("");

  useEffect(() => {
    if (user?.role !== "loading_clerk" && user?.role !== "admin") return;
    if (!id) return;
    setLoading(true);
    api
      .loadingSheet(Number(id), orderId)
      .then((data) => {
        setLines(data.lines);
        setLots(data.available_lots);
        setBatches(data.available_batches || []);
        setVehicleNo(data.trip.vehicle_no);
        setDriverName(data.trip.driver_name);
        const next: Record<number, Draft> = {};
        for (const line of data.lines) {
          next[line.id] = {
            assignment: assignmentFromLine(line),
            carton_weight_kg:
              line.carton_weight_kg != null ? String(line.carton_weight_kg) : "",
          };
        }
        setDrafts(next);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user, id, orderId]);

  const lotsByProduct = useMemo(() => {
    const map: Record<number, ReadyStockLot[]> = {};
    for (const lot of lots) {
      if (!map[lot.product_id]) map[lot.product_id] = [];
      map[lot.product_id].push(lot);
    }
    return map;
  }, [lots]);

  const batchesByProduct = useMemo(() => {
    const map: Record<number, ReadyStockBatchOption[]> = {};
    for (const b of batches) {
      if (b.product_id == null) continue;
      if (!map[b.product_id]) map[b.product_id] = [];
      map[b.product_id].push(b);
    }
    return map;
  }, [batches]);

  const assignedCount = useMemo(
    () =>
      Object.values(drafts).filter((d) => d.assignment && d.assignment !== "")
        .length,
    [drafts],
  );

  /** Bottles/sets drafted to each ready-stock lot on this sheet. */
  const draftNeedByLot = useMemo(() => {
    const need: Record<number, number> = {};
    for (const line of lines) {
      const a = drafts[line.id]?.assignment || "";
      if (!a.startsWith("lot:")) continue;
      const lotId = Number(a.slice(4));
      need[lotId] = (need[lotId] || 0) + line.bottles;
    }
    return need;
  }, [lines, drafts]);

  const lotById = useMemo(() => {
    const map: Record<number, ReadyStockLot> = {};
    for (const lot of lots) map[lot.id] = lot;
    return map;
  }, [lots]);

  function leftToAssign(lot: ReadyStockLot): number {
    const base =
      lot.available_to_assign != null ? lot.available_to_assign : lot.on_hand;
    return base - (draftNeedByLot[lot.id] || 0);
  }

  const stockOverAssign = useMemo(() => {
    const msgs: string[] = [];
    for (const [lotIdStr, need] of Object.entries(draftNeedByLot)) {
      const lot = lotById[Number(lotIdStr)];
      if (!lot) continue;
      const base =
        lot.available_to_assign != null ? lot.available_to_assign : lot.on_hand;
      if (need > base) {
        const unit = lot.unit_label || (lot.is_bundle ? "sets" : "bottles");
        msgs.push(
          `${lot.batch_label} (${lot.product_name}): need ${need} but only ${base} ${unit} left to assign`,
        );
      }
    }
    return msgs;
  }, [draftNeedByLot, lotById]);

  const weightWarningCount = useMemo(() => {
    const byBox = new Map<string, LoadingSheetLine[]>();
    for (const line of lines) {
      const key = `${line.order_id}:${line.box_no}`;
      if (!byBox.has(key)) byBox.set(key, []);
      byBox.get(key)!.push(line);
    }
    let n = 0;
    for (const boxLines of byBox.values()) {
      const first = boxLines[0];
      const entered = drafts[first.id]?.carton_weight_kg ?? "";
      if (weightWarning(boxLines, entered)) n += 1;
    }
    return n;
  }, [lines, drafts]);

  if (user && user.role !== "loading_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  function setDraft(lineId: number, field: keyof Draft, value: string) {
    setSavedNote("");
    setDrafts((prev) => ({
      ...prev,
      [lineId]: {
        assignment: prev[lineId]?.assignment ?? "",
        carton_weight_kg: prev[lineId]?.carton_weight_kg ?? "",
        [field]: value,
      },
    }));
  }

  async function saveProgress() {
    if (!id) return;
    if (weightWarningCount > 0) {
      setError("Fix the red carton weights before saving.");
      return;
    }
    if (stockOverAssign.length > 0) {
      setError(
        `Not enough ready stock left to assign: ${stockOverAssign.join("; ")}`,
      );
      return;
    }
    setSaving(true);
    setError("");
    setSavedNote("");
    try {
      const weightByBox = new Map<string, string>();
      for (const line of lines) {
        const key = `${line.order_id}:${line.box_no}`;
        if (!weightByBox.has(key)) {
          const wt = (drafts[line.id]?.carton_weight_kg || "").trim();
          weightByBox.set(key, wt);
        }
      }
      const payload = lines.map((line) => {
        const d = drafts[line.id] || { assignment: "", carton_weight_kg: "" };
        const wt = weightByBox.get(`${line.order_id}:${line.box_no}`) || "";
        let ready_stock_lot_id: number | null = null;
        let source_batch_id: number | null = null;
        if (d.assignment.startsWith("lot:")) {
          ready_stock_lot_id = Number(d.assignment.slice(4));
        } else if (d.assignment.startsWith("batch:")) {
          source_batch_id = Number(d.assignment.slice(6));
        }
        return {
          id: line.id,
          ready_stock_lot_id,
          source_batch_id,
          carton_weight_kg: wt === "" ? null : wt,
        };
      });
      const res = await api.saveLoadingSheet(Number(id), payload);
      setLines((prev) => {
        const byId = new Map(res.lines.map((l) => [l.id, l]));
        return prev.map((l) => byId.get(l.id) || l);
      });
      setSavedNote("Progress saved. You can leave and continue later.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  const groups = useMemo(() => {
    const byOrder = new Map<
      number,
      { po: string; customer: string; boxes: Map<number, LoadingSheetLine[]> }
    >();
    for (const line of lines) {
      if (!byOrder.has(line.order_id)) {
        byOrder.set(line.order_id, {
          po: line.po_number,
          customer: line.customer_name,
          boxes: new Map(),
        });
      }
      const g = byOrder.get(line.order_id)!;
      if (!g.boxes.has(line.box_no)) g.boxes.set(line.box_no, []);
      g.boxes.get(line.box_no)!.push(line);
    }
    return [...byOrder.entries()];
  }, [lines]);

  return (
    <div className="page loading-page loading-sheet-page">
      <div className="page-header">
        <div>
          <Link className="muted" to={`/loading/trips/${id}`}>
            ← Back to trip
          </Link>
          <h1>Vehicle loading sheet batch assignment</h1>
          <p className="muted">
            Vehicle {vehicleNo || "—"} · Driver {driverName || "—"} ·{" "}
            {assignedCount}/{lines.length} lines with batch
          </p>
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={saveProgress}
          disabled={
            saving ||
            loading ||
            weightWarningCount > 0 ||
            stockOverAssign.length > 0
          }
        >
          {saving ? "Saving…" : "Save progress"}
        </button>
      </div>

      <div className="info-banner">
        Prefer Ready stock when bottles are filled; otherwise assign an Esha
        batch. Ready stock “left to assign” drops as you assign (actual on-hand
        deducts only on delivery). Carton weight must be within ±8% to save.
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {stockOverAssign.length > 0 ? (
        <div className="error-banner">
          Not enough ready stock left to assign — {stockOverAssign.join("; ")}.
          Use another batch / Esha liquid, or fill more ready stock.
        </div>
      ) : null}
      {savedNote ? <div className="success-banner">{savedNote}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading && lines.length === 0 ? (
        <div className="empty-state">
          <p>No carton lines on this sheet yet.</p>
        </div>
      ) : null}

      {groups.map(([oid, group]) => (
        <section key={oid} className="card sheet-order-block">
          <h2>
            PO {group.po} — {group.customer}
          </h2>
          <div className="table-wrap">
            <table className="batch-table sheet-table">
              <thead>
                <tr>
                  <th>Box No</th>
                  <th>Product name</th>
                  <th>No of bottles</th>
                  <th>Batch no</th>
                  <th>Carton wt (kg)</th>
                  <th>PO no</th>
                  <th>Challan / DC</th>
                </tr>
              </thead>
              <tbody>
                {[...group.boxes.entries()].map(([boxNo, boxLines]) =>
                  boxLines.map((line, idx) => {
                    const draft = drafts[line.id] || {
                      assignment: "",
                      carton_weight_kg: "",
                    };
                    const lotOpts = lotsByProduct[line.product_id] || [];
                    const batchOpts = batchesByProduct[line.product_id] || [];
                    const warning =
                      idx === 0
                        ? weightWarning(boxLines, draft.carton_weight_kg)
                        : null;
                    const lotOver =
                      draft.assignment.startsWith("lot:") &&
                      (() => {
                        const lot = lotById[Number(draft.assignment.slice(4))];
                        if (!lot) return false;
                        const base =
                          lot.available_to_assign != null
                            ? lot.available_to_assign
                            : lot.on_hand;
                        return (draftNeedByLot[lot.id] || 0) > base;
                      })();
                    return (
                      <tr
                        key={line.id}
                        className={
                          warning || lotOver ? "row-invalid" : undefined
                        }
                      >
                        <td>{idx === 0 ? boxNo : ""}</td>
                        <td>{line.product_name}</td>
                        <td>{line.bottles}</td>
                        <td>
                          <select
                            className="sheet-select"
                            value={draft.assignment}
                            onChange={(e) =>
                              setDraft(line.id, "assignment", e.target.value)
                            }
                          >
                            <option value="">— assign batch</option>
                            {lotOpts.length > 0 ? (
                              <optgroup label="Ready stock">
                                {lotOpts.map((lot) => {
                                  const unit =
                                    lot.unit_label ||
                                    (lot.is_bundle ? "sets" : "bottles");
                                  const left = leftToAssign(lot);
                                  return (
                                    <option
                                      key={`lot-${lot.id}`}
                                      value={`lot:${lot.id}`}
                                    >
                                      {lot.batch_label} — {left} {unit} left to
                                      assign ({lot.on_hand} on hand)
                                    </option>
                                  );
                                })}
                              </optgroup>
                            ) : null}
                            {batchOpts.length > 0 ? (
                              <optgroup label="Esha batches">
                                {batchOpts.map((b) => (
                                  <option
                                    key={`batch-${b.id}`}
                                    value={`batch:${b.id}`}
                                  >
                                    {b.batch_number} —{" "}
                                    {Number(b.remaining_quantity)} L left
                                  </option>
                                ))}
                              </optgroup>
                            ) : null}
                          </select>
                        </td>
                        <td>
                          {idx === 0 ? (
                            <>
                              <input
                                className={
                                  warning
                                    ? "sheet-weight input-invalid"
                                    : "sheet-weight"
                                }
                                type="number"
                                min={0}
                                step="0.001"
                                value={draft.carton_weight_kg}
                                onChange={(e) =>
                                  setDraft(
                                    line.id,
                                    "carton_weight_kg",
                                    e.target.value,
                                  )
                                }
                                placeholder={
                                  boxLines.length === 1 &&
                                  line.standard_weight_kg != null
                                    ? `std ${Number(line.standard_weight_kg)} kg`
                                    : "kg"
                                }
                                title={
                                  line.standard_weight_kg != null
                                    ? `Standard ${Number(line.standard_weight_kg)} kg ±${line.weight_tolerance_pct}%`
                                    : undefined
                                }
                              />
                              {warning ? (
                                <div className="field-error">{warning}</div>
                              ) : null}
                              {lotOver ? (
                                <div className="field-error">
                                  This ready stock lot is over-assigned — not
                                  enough left to assign.
                                </div>
                              ) : null}
                            </>
                          ) : (
                            <>
                              <span className="muted">shared box</span>
                              {lotOver ? (
                                <div className="field-error">
                                  Over-assigned ready stock.
                                </div>
                              ) : null}
                            </>
                          )}
                        </td>
                        <td>{line.po_number}</td>
                        <td>{line.challan_no || "—"}</td>
                      </tr>
                    );
                  }),
                )}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      {!loading && lines.length > 0 ? (
        <div className="form-actions">
          <button
            type="button"
            className="btn primary"
            onClick={saveProgress}
            disabled={
              saving || weightWarningCount > 0 || stockOverAssign.length > 0
            }
          >
            {saving ? "Saving…" : "Save progress"}
          </button>
          <Link className="btn" to={`/loading/trips/${id}`}>
            Back to trip
          </Link>
        </div>
      ) : null}
    </div>
  );
}
