import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import type {
  AvailabilityValue,
  MarketVisitColumnGroup,
  MarketVisitStatus,
  MarketVisitStoreRow,
} from "../types";

function todayISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function emptyAvailability(codes: string[]): Record<string, AvailabilityValue> {
  return Object.fromEntries(codes.map((c) => [c, "" as AvailabilityValue]));
}

function emptyFacing(codes: string[]): Record<string, string> {
  return Object.fromEntries(codes.map((c) => [c, ""]));
}

function newStore(codes: string[]): MarketVisitStoreRow {
  return {
    key: crypto.randomUUID(),
    store_name: "",
    location: "",
    remarks: "",
    availability: emptyAvailability(codes),
    facing: emptyFacing(codes),
  };
}

export default function MarketVisitFormPage() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const { user } = useAuth();
  const canVisit = Boolean(user?.can_market_visit);

  const [visitDate, setVisitDate] = useState(todayISO());
  const [status, setStatus] = useState<MarketVisitStatus>("in_process");
  const [groups, setGroups] = useState<MarketVisitColumnGroup[]>([]);
  const [codes, setCodes] = useState<string[]>([]);
  const [stores, setStores] = useState<MarketVisitStoreRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const readOnly = !isNew && status === "submitted";

  const mapStoresFromApi = useCallback(
    (
      apiStores: {
        id: number;
        store_name: string;
        location: string;
        remarks: string;
        availability: Record<string, string>;
        facing: Record<string, number | null>;
      }[],
      columnCodes: string[],
    ) => {
      if (!apiStores.length) {
        return [newStore(columnCodes), newStore(columnCodes)];
      }
      return apiStores.map((s) => ({
        key: `store-${s.id}`,
        store_name: s.store_name,
        location: s.location || "",
        remarks: s.remarks || "",
        availability: {
          ...emptyAvailability(columnCodes),
          ...Object.fromEntries(
            columnCodes.map((code) => {
              const v = (s.availability?.[code] || "").toUpperCase();
              const avail: AvailabilityValue = v === "Y" || v === "N" ? v : "";
              return [code, avail];
            }),
          ),
        },
        facing: {
          ...emptyFacing(columnCodes),
          ...Object.fromEntries(
            columnCodes.map((code) => {
              const val = s.facing?.[code];
              return [code, val == null ? "" : String(val)];
            }),
          ),
        },
      }));
    },
    [],
  );

  useEffect(() => {
    if (!canVisit) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      setInfo("");
      try {
        const meta = await api.marketVisitColumns();
        if (cancelled) return;
        setGroups(meta.groups);
        const columnCodes = meta.columns.map((c) => c.code);
        setCodes(columnCodes);

        if (isNew) {
          setVisitDate(todayISO());
          setStatus("in_process");
          setStores([newStore(columnCodes), newStore(columnCodes)]);
        } else {
          const visit = await api.marketVisit(Number(id));
          if (cancelled) return;
          setVisitDate(visit.visit_date);
          setStatus(visit.status);
          setStores(mapStoresFromApi(visit.stores, columnCodes));
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
  }, [canVisit, id, isNew, mapStoresFromApi]);

  const filledStores = useMemo(
    () => stores.filter((s) => s.store_name.trim()),
    [stores],
  );

  function updateStore(key: string, patch: Partial<MarketVisitStoreRow>) {
    if (readOnly) return;
    setStores((prev) => prev.map((s) => (s.key === key ? { ...s, ...patch } : s)));
  }

  function setAvailability(key: string, code: string, value: AvailabilityValue) {
    if (readOnly) return;
    setStores((prev) =>
      prev.map((s) =>
        s.key !== key
          ? s
          : { ...s, availability: { ...s.availability, [code]: value } },
      ),
    );
  }

  function setFacing(key: string, code: string, value: string) {
    if (readOnly) return;
    setStores((prev) =>
      prev.map((s) =>
        s.key !== key ? s : { ...s, facing: { ...s.facing, [code]: value } },
      ),
    );
  }

  async function persist(action: "save" | "submit") {
    if (readOnly) return;
    setSaving(true);
    setError("");
    setInfo("");
    try {
      const payload = {
        visit_date: visitDate,
        action,
        stores: stores.map((s) => ({
          store_name: s.store_name,
          location: s.location,
          remarks: s.remarks,
          availability: s.availability,
          facing: Object.fromEntries(
            Object.entries(s.facing).map(([code, val]) => [
              code,
              val === "" ? null : Number(val),
            ]),
          ),
        })),
      };

      if (filledStores.length === 0) {
        if (!isNew) {
          await api.deleteMarketVisit(Number(id));
        }
        navigate("/market-visit");
        return;
      }

      const result = isNew
        ? await api.createMarketVisit(payload)
        : await api.updateMarketVisit(Number(id), payload);

      if (result && "deleted" in result && result.deleted) {
        navigate("/market-visit");
        return;
      }

      if (action === "save" && result && "id" in result && result.id) {
        setStatus(result.status);
        setInfo("Saved as In process. You can keep editing, then Submit when done.");
        if (isNew) {
          navigate(`/market-visit/${result.id}`, { replace: true });
        }
        return;
      }

      navigate("/market-visit");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (!canVisit) return <Navigate to="/orders" replace />;

  return (
    <div className="page market-page">
      <div className="page-header market-header">
        <div>
          <div className="eyebrow">MARKET VISIT</div>
          <h1 className="market-title">
            MARKET VISIT FORM DATED{" "}
            <input
              className="date-inline"
              type="date"
              value={visitDate}
              onChange={(e) => setVisitDate(e.target.value)}
              disabled={readOnly}
            />
          </h1>
          <p className="muted">
            {user?.first_name || user?.username} · {filledStores.length} stores entered
          </p>
        </div>
        <div className="market-badges">
          <span
            className={`status-pill ${
              status === "submitted" ? "submitted-pill" : "in-process-pill"
            }`}
          >
            {status === "submitted" ? "Submitted" : "In process"}
          </span>
          <Link className="btn" to="/market-visit">
            Back
          </Link>
          {!readOnly ? (
            <>
              <button
                type="button"
                className="btn"
                disabled={saving || loading}
                onClick={() => persist("save")}
              >
                {saving ? "Working…" : "Save"}
              </button>
              <button
                type="button"
                className="btn primary"
                disabled={saving || loading}
                onClick={() => persist("submit")}
              >
                {saving ? "Working…" : "Submit"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {info ? <div className="success-banner">{info}</div> : null}
      {readOnly ? (
        <div className="info-banner">Submitted — cannot edit again.</div>
      ) : null}
      {loading ? <p>Loading…</p> : null}

      {!loading ? (
        <>
          {!readOnly ? (
            <p className="help">
              Use <strong>Save</strong> to keep an in-process sheet you can edit later.
              Use <strong>Submit</strong> when finished — submitted sheets cannot be
              edited. Empty sheets are discarded.
            </p>
          ) : null}

          <section className="card market-card">
            <h2>Availability Yes / No</h2>
            <p className="help danger-help">
              Red cells = N (out of stock). Mark Y when fixed, then save or submit.
            </p>
            <MarketTable
              mode="availability"
              groups={groups}
              stores={stores}
              readOnly={readOnly}
              onStoreMeta={updateStore}
              onAvailability={setAvailability}
              onFacing={setFacing}
              onRemove={(key) =>
                setStores((prev) => prev.filter((s) => s.key !== key))
              }
            />
          </section>

          <section className="card market-card">
            <h2>Facing Display in Unit</h2>
            <MarketTable
              mode="facing"
              groups={groups}
              stores={stores}
              readOnly={readOnly}
              onStoreMeta={updateStore}
              onAvailability={setAvailability}
              onFacing={setFacing}
              onRemove={(key) =>
                setStores((prev) => prev.filter((s) => s.key !== key))
              }
            />
          </section>

          {!readOnly ? (
            <div className="form-actions">
              <button
                type="button"
                className="btn"
                onClick={() => setStores((prev) => [...prev, newStore(codes)])}
              >
                + Add store
              </button>
              <button
                type="button"
                className="btn"
                disabled={saving}
                onClick={() => persist("save")}
              >
                {saving ? "Working…" : "Save"}
              </button>
              <button
                type="button"
                className="btn primary"
                disabled={saving}
                onClick={() => persist("submit")}
              >
                {saving ? "Working…" : "Submit"}
              </button>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function MarketTable({
  mode,
  groups,
  stores,
  readOnly,
  onStoreMeta,
  onAvailability,
  onFacing,
  onRemove,
}: {
  mode: "availability" | "facing";
  groups: MarketVisitColumnGroup[];
  stores: MarketVisitStoreRow[];
  readOnly: boolean;
  onStoreMeta: (key: string, patch: Partial<MarketVisitStoreRow>) => void;
  onAvailability: (key: string, code: string, value: AvailabilityValue) => void;
  onFacing: (key: string, code: string, value: string) => void;
  onRemove: (key: string) => void;
}) {
  return (
    <div className="market-scroll">
      <table className="market-table">
        <thead>
          <tr>
            <th rowSpan={2} className="sticky-col">
              STORE NAME
            </th>
            <th rowSpan={2} className="sticky-col-2">
              Location
            </th>
            {groups.map((g) => (
              <th key={g.group} colSpan={g.columns.length} className="group-head">
                {g.group}
              </th>
            ))}
            <th rowSpan={2}>REMARKS</th>
            {!readOnly ? <th rowSpan={2} /> : null}
          </tr>
          <tr>
            {groups.flatMap((g) =>
              g.columns.map((c) => (
                <th key={c.code} className="sub-head">
                  {c.label}
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>
          {stores.map((store) => (
            <tr key={`${mode}-${store.key}`}>
              <td className="sticky-col">
                <input
                  value={store.store_name}
                  onChange={(e) =>
                    onStoreMeta(store.key, { store_name: e.target.value })
                  }
                  placeholder="Store name"
                  disabled={readOnly}
                />
              </td>
              <td className="sticky-col-2">
                <input
                  value={store.location}
                  onChange={(e) =>
                    onStoreMeta(store.key, { location: e.target.value })
                  }
                  placeholder="Location"
                  disabled={readOnly}
                />
              </td>
              {groups.flatMap((g) =>
                g.columns.map((c) => (
                  <td key={c.code}>
                    {mode === "availability" ? (
                      <select
                        className={
                          store.availability[c.code] === "N" ? "yn-n" : undefined
                        }
                        value={store.availability[c.code] || ""}
                        onChange={(e) =>
                          onAvailability(
                            store.key,
                            c.code,
                            e.target.value as AvailabilityValue,
                          )
                        }
                        disabled={readOnly}
                      >
                        <option value="">—</option>
                        <option value="Y">Y</option>
                        <option value="N">N</option>
                      </select>
                    ) : (
                      <input
                        className="facing-input"
                        type="number"
                        min={0}
                        value={store.facing[c.code] ?? ""}
                        onChange={(e) =>
                          onFacing(store.key, c.code, e.target.value)
                        }
                        disabled={readOnly}
                      />
                    )}
                  </td>
                )),
              )}
              <td>
                <input
                  value={store.remarks}
                  onChange={(e) =>
                    onStoreMeta(store.key, { remarks: e.target.value })
                  }
                  placeholder="Optional"
                  disabled={readOnly}
                />
              </td>
              {!readOnly ? (
                <td>
                  <button
                    type="button"
                    className="icon-btn"
                    onClick={() => onRemove(store.key)}
                    disabled={stores.length <= 1}
                    aria-label="Remove store"
                  >
                    ×
                  </button>
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
