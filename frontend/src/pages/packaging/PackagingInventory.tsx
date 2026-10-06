import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { PackagingMaterial } from "../../types";

type Draft = {
  purchased_qty: string;
  rejected_qty: string;
};

export default function PackagingInventoryPage() {
  const { user } = useAuth();
  const [materials, setMaterials] = useState<PackagingMaterial[]>([]);
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  async function load(nextSearch = search) {
    setLoading(true);
    setError("");
    try {
      const data = await api.packagingMaterials({
        search: nextSearch.trim() || undefined,
      });
      setMaterials(data);
      const next: Record<number, Draft> = {};
      for (const m of data) {
        next[m.id] = {
          purchased_qty: String(m.purchased_qty),
          rejected_qty: String(m.rejected_qty),
        };
      }
      setDrafts(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user?.role !== "batch_clerk" && user?.role !== "admin") return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  if (user && user.role !== "batch_clerk" && user.role !== "admin") {
    return <Navigate to="/orders" replace />;
  }

  function setDraft(id: number, field: keyof Draft, value: string) {
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        purchased_qty: prev[id]?.purchased_qty ?? "0",
        rejected_qty: prev[id]?.rejected_qty ?? "0",
        [field]: value,
      },
    }));
  }

  async function saveRow(m: PackagingMaterial) {
    const draft = drafts[m.id];
    if (!draft) return;
    const purchased = Number(draft.purchased_qty);
    const rejected = Number(draft.rejected_qty);
    if (!Number.isInteger(purchased) || purchased < 0) {
      setError("Purchased must be a non-negative whole number.");
      return;
    }
    if (!Number.isInteger(rejected) || rejected < 0) {
      setError("Rejected/damage must be a non-negative whole number.");
      return;
    }
    if (
      purchased === m.purchased_qty &&
      rejected === m.rejected_qty
    ) {
      return;
    }
    setSavingId(m.id);
    setError("");
    try {
      const updated = await api.updatePackagingMaterial(m.id, {
        purchased_qty: purchased,
        rejected_qty: rejected,
      });
      setMaterials((prev) =>
        prev.map((row) => (row.id === m.id ? updated : row)),
      );
      setDrafts((prev) => ({
        ...prev,
        [m.id]: {
          purchased_qty: String(updated.purchased_qty),
          rejected_qty: String(updated.rejected_qty),
        },
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSavingId(null);
    }
  }

  async function onRename(m: PackagingMaterial) {
    const next = window.prompt("Material name", m.name);
    if (next == null) return;
    const name = next.trim();
    if (!name || name === m.name) return;
    setError("");
    try {
      const updated = await api.updatePackagingMaterial(m.id, { name });
      setMaterials((prev) =>
        prev.map((row) => (row.id === m.id ? updated : row)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rename failed");
    }
  }

  async function onAddMaterial() {
    const name = window.prompt("New material name")?.trim();
    if (!name) return;
    setAdding(true);
    setError("");
    try {
      await api.createPackagingMaterial({ name });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Add failed");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="page batch-page packaging-page">
      <div className="page-header">
        <div>
          <h1>Packaging inventory</h1>
          <p className="muted">
            Balance = Purchased − Rejected/Damage − UIP. UIP stays 0 until
            filling/delivered orders start deducting later.
          </p>
        </div>
        <button
          type="button"
          className="btn primary pill-btn"
          onClick={onAddMaterial}
          disabled={adding}
        >
          {adding ? "Adding…" : "Add material"}
        </button>
      </div>

      <div className="batch-toolbar">
        <input
          className="search-input"
          placeholder="FIND MATERIAL"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") load();
          }}
        />
        <button type="button" className="btn" onClick={() => load()}>
          Search
        </button>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="card table-wrap">
        <table className="batch-table packaging-table">
          <thead>
            <tr>
              <th>Material</th>
              <th>Purchased</th>
              <th>Rejected / Damage</th>
              <th>UIP</th>
              <th>Balance</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {!loading && materials.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted">
                  No packaging materials found.
                </td>
              </tr>
            ) : null}
            {materials.map((m) => {
              const draft = drafts[m.id] || {
                purchased_qty: String(m.purchased_qty),
                rejected_qty: String(m.rejected_qty),
              };
              const dirty =
                Number(draft.purchased_qty) !== m.purchased_qty ||
                Number(draft.rejected_qty) !== m.rejected_qty;
              return (
                <tr key={m.id}>
                  <td>
                    <button
                      type="button"
                      className="linkish"
                      onClick={() => onRename(m)}
                      title="Click to rename"
                    >
                      {m.name}
                    </button>
                    <div className="muted code-under">{m.code}</div>
                  </td>
                  <td>
                    <input
                      className="qty-input"
                      type="number"
                      min={0}
                      step={1}
                      value={draft.purchased_qty}
                      onChange={(e) =>
                        setDraft(m.id, "purchased_qty", e.target.value)
                      }
                      onBlur={() => saveRow(m)}
                    />
                  </td>
                  <td>
                    <input
                      className="qty-input"
                      type="number"
                      min={0}
                      step={1}
                      value={draft.rejected_qty}
                      onChange={(e) =>
                        setDraft(m.id, "rejected_qty", e.target.value)
                      }
                      onBlur={() => saveRow(m)}
                    />
                  </td>
                  <td>
                    <input
                      className="qty-input"
                      type="number"
                      value={m.uip_qty}
                      disabled
                      readOnly
                      title="UIP is read-only until order deduction is built"
                    />
                  </td>
                  <td className="balance-cell">{m.balance}</td>
                  <td>
                    <button
                      type="button"
                      className="btn"
                      disabled={!dirty || savingId === m.id}
                      onClick={() => saveRow(m)}
                    >
                      {savingId === m.id ? "Saving…" : "Save"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {loading ? <p className="muted">Loading…</p> : null}
    </div>
  );
}
