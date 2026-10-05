import { useEffect, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import type { MarketVisitListItem, MarketVisitStatus } from "../types";

type TabFilter = "all" | MarketVisitStatus;

function formatDate(iso: string) {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function MarketVisitListPage() {
  const { user } = useAuth();
  const [visits, setVisits] = useState<MarketVisitListItem[]>([]);
  const [tab, setTab] = useState<TabFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user?.can_market_visit) return;
    setLoading(true);
    api
      .marketVisits()
      .then(setVisits)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [user]);

  const filtered = useMemo(() => {
    if (tab === "all") return visits;
    return visits.filter((v) => v.status === tab);
  }, [visits, tab]);

  if (!user?.can_market_visit) {
    return <Navigate to="/orders" replace />;
  }

  return (
    <div className="page market-list-page">
      <div className="page-header">
        <div>
          <h1>Market visits</h1>
          <div className="filter-tabs">
            {(
              [
                ["all", "All"],
                ["in_process", "In process"],
                ["submitted", "Submitted"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`filter-tab${tab === value ? " active" : ""}`}
                onClick={() => setTab(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <p className="muted">
            {loading
              ? "Loading…"
              : `Showing ${filtered.length} of ${visits.length} visits.`}
          </p>
        </div>
        <Link className="btn primary pill-btn" to="/market-visit/new">
          New market visit
        </Link>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      {!loading && filtered.length === 0 ? (
        <div className="empty-state">
          <p>
            {tab === "in_process"
              ? "No in-process visits."
              : tab === "submitted"
                ? "No submitted visits."
                : "No market visits yet."}
          </p>
          <Link className="btn primary" to="/market-visit/new">
            New market visit
          </Link>
        </div>
      ) : null}

      <div className="visit-card-list">
        {filtered.map((visit) => (
          <Link
            key={visit.id}
            to={`/market-visit/${visit.id}`}
            className="visit-card"
          >
            <div className="visit-card-top">
              <h2>{visit.title}</h2>
              <span
                className={`status-pill ${
                  visit.status === "submitted"
                    ? "submitted-pill"
                    : "in-process-pill"
                }`}
              >
                {visit.status === "submitted" ? "Submitted" : "In process"}
              </span>
            </div>
            <p className="visit-card-meta">
              {visit.first_location ? `${visit.first_location} · ` : ""}
              {formatDate(visit.visit_date)}
            </p>
            <p className="visit-card-footer">
              {visit.store_count} store{visit.store_count === 1 ? "" : "s"} ·{" "}
              {visit.created_by_username} · {formatDate(visit.visit_date)}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
