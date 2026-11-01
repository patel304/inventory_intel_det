import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Building2,
  ClipboardList,
  Package,
  ShieldAlert,
  ShoppingBag,
  TrendingDown,
} from "lucide-react";
import api, { getErrorMessage, getList } from "../services/api";
import StatCard from "../components/StatCard";
import Badge from "../components/Badge";
import { EmptyState, ErrorBanner, LoadingState } from "../components/Feedback";

export default function Dashboard({ onOpenAlert }) {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [summaryResponse, alertsResponse] = await Promise.all([
          api.get("/dashboard/summary"),
          api.get("/alerts", { params: { page: 1, page_size: 8 } }),
        ]);
        setSummary(summaryResponse.data);
        setAlerts(getList(alertsResponse.data));
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <LoadingState label="Loading dashboard..." />;

  return (
    <>
      <ErrorBanner message={error} />
      {summary && (
        <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatCard title="Total Stores" value={summary.stores} icon={Building2} color="blue" />
          <StatCard title="Total SKUs" value={summary.skus} icon={ShoppingBag} color="violet" />
          <StatCard title="Inventory Movements" value={summary.inventory_movements} icon={Package} color="slate" />
          <StatCard title="Cycle Counts" value={summary.cycle_counts} icon={ClipboardList} color="green" />
          <StatCard title="Total Alerts" value={summary.alerts_total} icon={AlertTriangle} color="amber" />
          <StatCard title="Open Alerts" value={summary.alerts_open} icon={ShieldAlert} color="red" />
          <StatCard title="Critical Alerts" value={summary.alerts_critical} icon={TrendingDown} color="red" />
          <StatCard title="Investigations In Progress" value={summary.investigations_in_progress} icon={ClipboardList} color="violet" />
          <StatCard title="Resolved Investigations" value={summary.investigations_resolved} icon={ClipboardList} color="green" />
        </div>
      )}

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 p-5">
          <h3 className="font-bold text-slate-900">Recent shrinkage alerts</h3>
          <p className="mt-1 text-xs text-slate-500">Latest alerts from the detection pipeline</p>
        </div>
        {alerts.length === 0 ? (
          <div className="p-6">
            <EmptyState title="No alerts yet" detail="Run detection or wait for cycle-count shortages." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  {["Alert", "Store", "SKU", "Variance", "Severity", "Status"].map((heading) => (
                    <th key={heading} className="px-5 py-4">{heading}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {alerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className="cursor-pointer hover:bg-blue-50"
                    onClick={() => onOpenAlert?.(alert)}
                  >
                    <td className="px-5 py-4 font-semibold text-blue-700">{alert.alert_code}</td>
                    <td className="px-5 py-4">{alert.store_code || alert.store_id}</td>
                    <td className="px-5 py-4">{alert.sku_code || alert.sku_id}</td>
                    <td className="px-5 py-4">{alert.variance_quantity ?? alert.variance ?? "—"}</td>
                    <td className="px-5 py-4"><Badge value={alert.severity} /></td>
                    <td className="px-5 py-4"><Badge value={alert.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
