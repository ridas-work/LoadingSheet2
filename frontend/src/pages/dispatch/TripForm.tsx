import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import type { DispatchOrder, Trip } from "../../types";

type PoolOrder = {
  id: number;
  po_number: string;
  customer_name: string;
  city: string;
  deadline_date: string;
  created_by_username: string;
};

export default function TripFormPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const isEdit = Boolean(id) && id !== "new";

  const [pool, setPool] = useState<PoolOrder[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [challans, setChallans] = useState<Record<number, string>>({});
  const [vehicleNo, setVehicleNo] = useState("");
  const [driverName, setDriverName] = useState("");
  const [helperName, setHelperName] = useState("");
  const [productionIncharge, setProductionIncharge] = useState("");
  const [security, setSecurity] = useState("");
  const [defaultChallan, setDefaultChallan] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const selectedOrders = useMemo(
    () => pool.filter((o) => selected.includes(o.id)),
    [pool, selected],
  );

  useEffect(() => {
    if (user?.role !== "dispatch_clerk" && user?.role !== "admin") return;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const pending = await api.dispatchOrders();
        let poolOrders: PoolOrder[] = pending.map((o: DispatchOrder) => ({
          id: o.id,
          po_number: o.po_number,
          customer_name: o.customer_name,
          city: o.city,
          deadline_date: o.deadline_date,
          created_by_username: o.created_by_username,
        }));

        if (isEdit && id) {
          const trip: Trip = await api.trip(Number(id));
          setVehicleNo(trip.vehicle_no);
          setDriverName(trip.driver_name);
          setHelperName(trip.helper_name);
          setProductionIncharge(trip.production_incharge);
          setSecurity(trip.security);
          setDefaultChallan(trip.default_challan_no);
          const tripPool: PoolOrder[] = trip.trip_orders.map((to) => ({
            id: to.order_id,
            po_number: to.po_number,
            customer_name: to.customer_name,
            city: to.city,
            deadline_date: to.deadline_date,
            created_by_username: to.created_by_username,
          }));
          const pendingIds = new Set(poolOrders.map((o) => o.id));
          for (const o of tripPool) {
            if (!pendingIds.has(o.id)) poolOrders.push(o);
          }
          setSelected(trip.trip_orders.map((to) => to.order_id));
          const nextChallans: Record<number, string> = {};
          for (const to of trip.trip_orders) {
            nextChallans[to.order_id] = to.challan_no || "";
          }
          setChallans(nextChallans);
        } else {
          const preset = (searchParams.get("orders") || "")
            .split(",")
            .map((x) => Number(x.trim()))
            .filter((n) => Number.isInteger(n) && n > 0);
          const valid = preset.filter((oid) =>
            poolOrders.some((o) => o.id === oid),
          );
          setSelected(valid);
        }

        setPool(poolOrders);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [user, id, isEdit, searchParams]);

  if (user && user.role !== "dispatch_clerk" && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  function toggle(orderId: number) {
    setSelected((prev) =>
      prev.includes(orderId)
        ? prev.filter((x) => x !== orderId)
        : [...prev, orderId],
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (selected.length === 0) {
      setError("Select at least one order for this vehicle.");
      return;
    }
    setSaving(true);
    setError("");
    const payload = {
      vehicle_no: vehicleNo.trim(),
      driver_name: driverName.trim(),
      helper_name: helperName.trim(),
      production_incharge: productionIncharge.trim(),
      security: security.trim(),
      default_challan_no: defaultChallan.trim(),
      orders: selected.map((orderId) => ({
        order_id: orderId,
        challan_no: (challans[orderId] || "").trim(),
      })),
    };
    try {
      if (isEdit && id) {
        await api.updateTrip(Number(id), payload);
      } else {
        await api.createTrip(payload);
      }
      navigate("/dispatch/trips");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page dispatch-page">
      <div className="page-header">
        <div>
          <h1>{isEdit ? `Edit trip #${id}` : "New dispatch trip"}</h1>
          <p className="muted">
            Select one or more POs for the same truck, set per-PO challans, then
            vehicle details.
          </p>
        </div>
        <Link className="btn" to="/dispatch/trips">
          Back to trips
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading ? <p className="muted">Loading…</p> : null}

      {!loading ? (
        <form className="dispatch-form" onSubmit={onSubmit}>
          <section className="card">
            <h2>Orders on this vehicle</h2>
            <p className="muted">Select one or more POs for the same truck.</p>
            <div className="dispatch-check-list">
              {pool.length === 0 ? (
                <p className="muted">No available orders.</p>
              ) : null}
              {pool.map((o) => (
                <label key={o.id} className="dispatch-check-row">
                  <input
                    type="checkbox"
                    checked={selected.includes(o.id)}
                    onChange={() => toggle(o.id)}
                  />
                  <span>
                    {o.po_number} — {o.customer_name}
                  </span>
                </label>
              ))}
            </div>
          </section>

          {selectedOrders.length > 0 ? (
            <section className="card">
              <h2>Challan / DC number for each PO</h2>
              <p className="muted">
                These numbers print separately on the combined vehicle loading
                sheet.
              </p>
              {selectedOrders.map((o) => (
                <label key={o.id}>
                  {o.po_number} — {o.customer_name}
                  <input
                    value={challans[o.id] || ""}
                    onChange={(e) =>
                      setChallans((prev) => ({
                        ...prev,
                        [o.id]: e.target.value,
                      }))
                    }
                    placeholder="Challan / DC no"
                  />
                </label>
              ))}
            </section>
          ) : null}

          <section className="card">
            <h2>Vehicle &amp; dispatch</h2>
            <p className="muted">
              Pick vehicle and driver from the fleet list. These fields sync to
              every selected PO&apos;s loading sheet.
            </p>
            <div className="row-2">
              <label>
                Vehicle no
                <input
                  value={vehicleNo}
                  onChange={(e) => setVehicleNo(e.target.value)}
                  placeholder="Pick a vehicle or type a new plate"
                />
              </label>
              <label>
                Driver name
                <input
                  value={driverName}
                  onChange={(e) => setDriverName(e.target.value)}
                  placeholder="Pick a driver or type a new name"
                />
              </label>
              <label>
                Default challan / DC no
                <input
                  value={defaultChallan}
                  onChange={(e) => setDefaultChallan(e.target.value)}
                />
              </label>
              <label>
                Helper name
                <input
                  value={helperName}
                  onChange={(e) => setHelperName(e.target.value)}
                />
              </label>
              <label>
                Production incharge
                <input
                  value={productionIncharge}
                  onChange={(e) => setProductionIncharge(e.target.value)}
                />
              </label>
              <label>
                Security
                <input
                  value={security}
                  onChange={(e) => setSecurity(e.target.value)}
                />
              </label>
            </div>
          </section>

          <div className="form-actions">
            <button type="submit" className="btn primary" disabled={saving}>
              {saving ? "Saving…" : isEdit ? "Save trip" : "Create trip"}
            </button>
            <Link className="btn" to="/dispatch">
              Cancel
            </Link>
          </div>
        </form>
      ) : null}
    </div>
  );
}
