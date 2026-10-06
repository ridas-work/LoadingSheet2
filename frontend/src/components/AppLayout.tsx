import { Link, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth";
import { homeForRole } from "../roleHome";

export default function AppLayout() {
  const { user, loading, logout } = useAuth();

  if (loading) return <div className="page">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;

  const home = homeForRole(user.role);
  const isBatchClerk = user.role === "batch_clerk";
  const isDispatchClerk = user.role === "dispatch_clerk";
  const isLoadingClerk = user.role === "loading_clerk";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <Link to={home}>Loading Sheet</Link>
          <span className="badge">{user.role}</span>
        </div>
        <nav>
          {isBatchClerk ? (
            <>
              <Link to="/batches">Active batches</Link>
              <Link to="/batches/new">New batch</Link>
              <Link to="/packaging">Packaging</Link>
            </>
          ) : null}
          {isDispatchClerk ? (
            <>
              <Link to="/dispatch">Orders</Link>
              <Link to="/dispatch/trips">Dispatch trips</Link>
            </>
          ) : null}
          {isLoadingClerk ? (
            <>
              <Link to="/loading">Trips &amp; batches</Link>
              <Link to="/loading/pending">Pending POs</Link>
              <Link to="/loading/ready-stock">Ready stock</Link>
            </>
          ) : null}
          {!isBatchClerk && !isDispatchClerk && !isLoadingClerk ? (
            <>
              <Link to="/orders">Orders</Link>
              <Link to="/orders/new">New order</Link>
              {user.can_market_visit ? (
                <Link to="/market-visit">Market Visit</Link>
              ) : null}
            </>
          ) : null}
        </nav>
        <div className="user-chip">
          <span>{user.first_name || user.username}</span>
          <button type="button" className="btn" onClick={() => logout()}>
            Log out
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
