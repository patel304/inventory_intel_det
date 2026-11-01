
import { useEffect, useState } from "react";
import {
  LayoutDashboard, AlertTriangle, ClipboardList,
  BarChart3, Search, Package, ShieldCheck,
  Menu, X, History, RefreshCw,
  Store as StoreIcon, Boxes, Warehouse, BrainCircuit, Activity
} from "lucide-react";
import api, { getErrorMessage } from "./services/api";
import Dashboard from "./pages/Dashboard";
import Stores from "./pages/Stores";

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Shrinkage Alerts", icon: AlertTriangle },
  { name: "Investigations", icon: ClipboardList },
  { name: "Stores", icon: StoreIcon },
  { name: "Products / SKUs", icon: Boxes },
  { name: "Inventory Lookup", icon: Warehouse },
  { name: "Model Performance", icon: BrainCircuit },
  { name: "System Health", icon: Activity },
  { name: "Analytics", icon: BarChart3 },
];

function getList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.investigations)) return data.investigations;
  if (Array.isArray(data?.events)) return data.events;
  return [];
}

export default function App() {
  const [page, setPage] = useState("Dashboard");
  const [alerts, setAlerts] = useState([]);
  const [alertTotal, setAlertTotal] = useState(0);
  const [alertPage, setAlertPage] = useState(1);
  const [investigations, setInvestigations] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);
  const [events, setEvents] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [skus, setSkus] = useState([]);
  const [skuTotal, setSkuTotal] = useState(0);
  const [skuPage, setSkuPage] = useState(1);
  const [skuSearch, setSkuSearch] = useState("");

  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [mobileMenu, setMobileMenu] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const [assignedTo, setAssignedTo] = useState("");
  const [findings, setFindings] = useState("");
  const [resolution, setResolution] = useState("");
  const [performedBy, setPerformedBy] = useState("");
  const [investigationStatus, setInvestigationStatus] =
    useState("IN_PROGRESS");

  async function fetchAlerts() {
    const response = await api.get("/alerts", {
      params: {
        page: alertPage,
        page_size: 25,
        search: searchTerm || undefined,
        severity: severityFilter === "ALL" ? undefined : severityFilter,
        status: statusFilter === "ALL" ? undefined : statusFilter,
      },
    });
    setAlerts(getList(response.data));
    setAlertTotal(response.data.total ?? 0);
  }

  async function fetchInvestigations() {
    const response = await api.get("/investigations");
    setInvestigations(getList(response.data));
  }

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError("");
      try {
        if (page === "Shrinkage Alerts") {
          await fetchAlerts();
        }
        if (page === "Investigations") {
          await fetchInvestigations();
        }
        if (page === "Analytics") {
          const response = await api.get("/analytics/summary");
          setAnalyticsData(response.data);
        }
        if (page === "Products / SKUs") {
          const response = await api.get("/skus", {
            params: { page: skuPage, page_size: 20, search: skuSearch || undefined },
          });
          setSkus(getList(response.data));
          setSkuTotal(response.data.total ?? 0);
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [page, skuPage, skuSearch, alertPage, searchTerm, severityFilter, statusFilter]);

  async function createInvestigation(alert) {
    setActionLoading(true);
    setError("");
    setMessage("");

    try {
      await api.post("/investigations", {
        alert_id: alert.id,
        assigned_to: assignedTo.trim() || null,
      });

      setSelectedAlert(null);
      setAssignedTo("");
      setMessage("Investigation created successfully.");
      await fetchAlerts();
      await fetchInvestigations();
      setPage("Investigations");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Could not create investigation."
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function openInvestigation(item) {
    setSelectedInvestigation(item);
    setFindings(item.findings || "");
    setResolution(item.resolution || "");
    setInvestigationStatus(item.status || "IN_PROGRESS");
    setPerformedBy("");
    setEvents([]);
    setError("");

    try {
      const response = await api.get(
        `/investigations/${item.id}/events`
      );
      setEvents(getList(response.data));
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load investigation event history."
      );
    }
  }

  async function saveInvestigation() {
    if (!selectedInvestigation) return;

    setActionLoading(true);
    setError("");
    setMessage("");

    try {
      await api.put(
        `/investigations/${selectedInvestigation.id}`,
        {
          findings,
          resolution,
          status: investigationStatus,
          performed_by: performedBy.trim() || null,
        }
      );

      await fetchInvestigations();
      await fetchAlerts();

      const updated = {
        ...selectedInvestigation,
        findings,
        resolution,
        status: investigationStatus,
      };

      setSelectedInvestigation(updated);

      const response = await api.get(
        `/investigations/${updated.id}/events`
      );
      setEvents(getList(response.data));

      setMessage("Investigation updated successfully.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to update investigation."
      );
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">

      {mobileMenu && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setMobileMenu(false)}
        />
      )}

      <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-950 text-white transition-transform lg:translate-x-0 ${
        mobileMenu ? "translate-x-0" : "-translate-x-full"
      }`}>
        <div className="border-b border-slate-800 px-6 py-7">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-600 p-2">
              <Package size={23} />
            </div>
            <div>
              <h1 className="text-xl font-bold">StockGuard</h1>
              <p className="text-xs text-slate-400">
                Inventory Intelligence
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-7">
          <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Workspace
          </p>

          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              onClick={() => {
                setPage(name);
                setMobileMenu(false);
                setSelectedAlert(null);
                setSelectedInvestigation(null);
                setMessage("");
                setError("");
              }}
              className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                page === name
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon size={19} />
              {name}
            </button>
          ))}
        </nav>

        <div className="border-t border-slate-800 p-5">
          <div className="flex items-center gap-3 rounded-xl bg-slate-900 p-3">
            <ShieldCheck className="text-emerald-400" size={22} />
            <div>
              <p className="text-sm font-semibold">System Status</p>
              <p className="text-xs text-emerald-400">
                Monitoring Active
              </p>
            </div>
          </div>
        </div>
      </aside>

      <main className="min-h-screen lg:ml-64">
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/90 px-5 py-4 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden"
              onClick={() => setMobileMenu(true)}
            >
              <Menu size={23} />
            </button>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {page}
              </h2>
              <p className="hidden text-xs text-slate-500 sm:block">
                Inventory shrinkage detection platform
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden items-center gap-2 text-xs font-medium text-emerald-600 sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              System Online
            </span>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-700">
              SG
            </div>
          </div>
        </header>

        <div className="p-5 md:p-8">
          <div className="mb-7">
            <h1 className="text-2xl font-bold text-slate-900">
              {page}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Monitor inventory risks and shrinkage activity.
            </p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {message && (
            <div className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
              {message}
            </div>
          )}

          {loading ? (
            <div className="rounded-xl border bg-white p-10 text-center text-slate-500">
              Loading data...
            </div>
          ) : (
            <>
              {page === "Dashboard" && (
                <Dashboard onOpenAlert={setSelectedAlert} />
              )}

              {page === "Stores" && <Stores />}

              {page === "Inventory Lookup" && <InventoryLookup />}

              {page === "Model Performance" && <ModelPerformance />}

              {page === "System Health" && <SystemHealth />}

              {page === "Products / SKUs" && (
                <SkuCatalog
                  items={skus}
                  total={skuTotal}
                  page={skuPage}
                  search={skuSearch}
                  onSearch={(value) => { setSkuPage(1); setSkuSearch(value); }}
                  onPage={setSkuPage}
                />
              )}

              {page === "Shrinkage Alerts" && (
                <AlertTable
                  alerts={alerts}
                  total={alertTotal}
                  page={alertPage}
                  onPage={setAlertPage}
                  onSelect={setSelectedAlert}
                  searchTerm={searchTerm}
                  setSearchTerm={(value) => { setAlertPage(1); setSearchTerm(value); }}
                  severityFilter={severityFilter}
                  setSeverityFilter={(value) => { setAlertPage(1); setSeverityFilter(value); }}
                  statusFilter={statusFilter}
                  setStatusFilter={(value) => { setAlertPage(1); setStatusFilter(value); }}
                />
              )}

              {page === "Investigations" && (
                <InvestigationTable
                  investigations={investigations}
                  onSelect={openInvestigation}
                  onRefresh={fetchInvestigations}
                />
              )}

              {page === "Analytics" && (
                <Analytics data={analyticsData} />
              )}
            </>
          )}
        </div>
      </main>

      {selectedAlert && (
        <AlertDetails
          alert={selectedAlert}
          assignedTo={assignedTo}
          setAssignedTo={setAssignedTo}
          onClose={() => setSelectedAlert(null)}
          onCreate={() => createInvestigation(selectedAlert)}
          loading={actionLoading}
        />
      )}

      {selectedInvestigation && (
        <InvestigationDetails
          item={selectedInvestigation}
          findings={findings}
          setFindings={setFindings}
          resolution={resolution}
          setResolution={setResolution}
          status={investigationStatus}
          setStatus={setInvestigationStatus}
          performedBy={performedBy}
          setPerformedBy={setPerformedBy}
          events={events}
          onSave={saveInvestigation}
          onClose={() => setSelectedInvestigation(null)}
          loading={actionLoading}
        />
      )}
    </div>
  );
}

function Badge({ value }) {
  const color = {
    HIGH: "bg-red-100 text-red-700",
    MEDIUM: "bg-amber-100 text-amber-700",
    LOW: "bg-emerald-100 text-emerald-700",
    OPEN: "bg-blue-100 text-blue-700",
    INVESTIGATING: "bg-violet-100 text-violet-700",
    IN_PROGRESS: "bg-violet-100 text-violet-700",
    RESOLVED: "bg-emerald-100 text-emerald-700",
    CLOSED: "bg-slate-100 text-slate-600",
  }[value] || "bg-slate-100 text-slate-600";

  return (
    <span className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${color}`}>
      {value || "—"}
    </span>
  );
}

function AlertTable({
  alerts,
  total,
  page,
  onPage,
  onSelect,
  searchTerm,
  setSearchTerm,
  severityFilter,
  setSeverityFilter,
  statusFilter,
  setStatusFilter,
}) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 p-5">
        <h3 className="font-bold text-slate-900">Shrinkage Alerts</h3>
        <p className="mb-5 mt-1 text-xs text-slate-500">
          Search and filter inventory discrepancies
        </p>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="relative">
            <Search className="absolute left-3 top-3 text-slate-400" size={17} />
            <input
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search alert, store or SKU..."
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
          >
            <option value="ALL">All Severities</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>

        <div className="mt-4 flex justify-between text-sm">
          <span className="text-slate-500">
            Showing {alerts.length} of {total} alerts · Page {page} of {Math.max(1, Math.ceil(total / 25))}
          </span>
          <button
            onClick={() => {
              setSearchTerm("");
              setSeverityFilter("ALL");
              setStatusFilter("ALL");
            }}
            className="font-semibold text-blue-600"
          >
            Clear filters
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              {["Alert ID", "Store", "SKU", "Variance", "Severity", "Status"].map(x => (
                <th key={x} className="whitespace-nowrap px-5 py-4">{x}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {alerts.map(alert => (
              <tr
                key={alert.id}
                onClick={() => onSelect(alert)}
                className="cursor-pointer hover:bg-blue-50"
              >
                <td className="px-5 py-4 font-semibold text-blue-700">{alert.alert_code}</td>
                <td className="px-5 py-4">{alert.store_code || alert.store_name || alert.store_id}</td>
                <td className="px-5 py-4">{alert.sku_code || alert.sku_name || alert.sku_id}</td>
                <td className="px-5 py-4">{alert.variance}</td>
                <td className="px-5 py-4"><Badge value={alert.severity} /></td>
                <td className="px-5 py-4"><Badge value={alert.status} /></td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr>
                <td colSpan="6" className="p-8 text-center text-slate-500">
                  No matching alerts found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm">
        <button disabled={page <= 1} onClick={() => onPage(page - 1)} className="rounded-lg border px-3 py-1 disabled:opacity-40">Previous</button>
        <span className="text-slate-500">Page {page} of {Math.max(1, Math.ceil(total / 25))}</span>
        <button disabled={page >= Math.ceil(total / 25)} onClick={() => onPage(page + 1)} className="rounded-lg border px-3 py-1 disabled:opacity-40">Next</button>
      </div>
    </section>
  );
}

function AlertDetails({
  alert, assignedTo, setAssignedTo,
  onClose, onCreate, loading
}) {
  const fields = [
    ["Alert ID", alert.alert_code],
    ["Store ID", alert.store_id],
    ["SKU ID", alert.sku_id],
    ["Detection Rule", alert.detection_rule],
    ["Expected Quantity", alert.expected_quantity],
    ["Observed Quantity", alert.observed_quantity],
    ["Variance", alert.variance],
    ["Confidence Score", alert.confidence_score],
    ["Estimated Loss (unit-cost basis)", alert.estimated_loss],
    ["Severity", alert.severity],
    ["Status", alert.status],
    ["Detected At", alert.detected_at
      ? new Date(alert.detected_at).toLocaleString()
      : "—"],
  ];

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 p-4" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Alert Details</h2>
            <p className="mt-1 text-sm text-slate-500">{alert.alert_code}</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100">
            <X size={20} />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {fields.map(([label, value]) => (
            <div key={label} className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-2 break-words text-sm font-semibold">
                {value ?? "—"}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-6 border-t pt-5">
          <h3 className="mb-3 font-bold">Start Investigation</h3>
          <label className="mb-2 block text-sm text-slate-600">
            Assigned To (optional)
          </label>
          <input
            value={assignedTo}
            onChange={e => setAssignedTo(e.target.value)}
            placeholder="Enter manager or employee name"
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-blue-500"
          />
          <div className="mt-5 flex flex-wrap justify-between gap-3">
            <Badge value={alert.severity} />
            <div className="flex gap-2">
              <button onClick={onClose} className="rounded-lg border px-4 py-2 text-sm">
                Close
              </button>
              <button
                disabled={loading}
                onClick={onCreate}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {loading ? "Creating..." : "Start Investigation"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InvestigationTable({ investigations, onSelect, onRefresh }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b p-5">
        <div>
          <h3 className="font-bold">Investigation Management</h3>
          <p className="mt-1 text-xs text-slate-500">
            Select an investigation to update or view its history
          </p>
        </div>
        <button onClick={onRefresh} className="rounded-lg border p-2 hover:bg-slate-50">
          <RefreshCw size={17} />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              {["Investigation ID", "Alert ID", "Assigned To", "Status", "Created At", "Action"].map(x => (
                <th key={x} className="whitespace-nowrap px-5 py-4">{x}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {investigations.map(item => (
              <tr key={item.id} className="hover:bg-blue-50/50">
                <td className="px-5 py-4 font-semibold">{item.investigation_code}</td>
                <td className="px-5 py-4">{item.alert_id}</td>
                <td className="px-5 py-4">{item.assigned_to || "Unassigned"}</td>
                <td className="px-5 py-4"><Badge value={item.status} /></td>
                <td className="px-5 py-4">
                  {item.created_at
                    ? new Date(item.created_at).toLocaleDateString()
                    : "—"}
                </td>
                <td className="px-5 py-4">
                  <button
                    onClick={() => onSelect(item)}
                    className="rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
            {investigations.length === 0 && (
              <tr>
                <td colSpan="6" className="p-8 text-center text-slate-500">
                  No investigations found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function InvestigationDetails({
  item, findings, setFindings,
  resolution, setResolution,
  status, setStatus,
  performedBy, setPerformedBy,
  events, onSave, onClose, loading
}) {
  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/50 p-4" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Investigation Details</h2>
            <p className="mt-1 text-sm text-slate-500">
              {item.investigation_code}
            </p>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-slate-100">
            <X size={20} />
          </button>
        </div>

        <div className="mb-5 flex flex-wrap items-center gap-3">
          <Badge value={status} />
          <span className="text-sm text-slate-500">
            Related Alert ID: {item.alert_id}
          </span>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium">
              Investigation Findings
            </label>
            <textarea
              rows="3"
              value={findings}
              onChange={e => setFindings(e.target.value)}
              placeholder="Describe what was discovered..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              Resolution
            </label>
            <textarea
              rows="3"
              value={resolution}
              onChange={e => setResolution(e.target.value)}
              placeholder="Describe the corrective action..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium">
                Status
              </label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                className="w-full rounded-xl border border-slate-200 p-3 text-sm"
              >
                <option value="IN_PROGRESS">In Progress</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                Updated By (optional)
              </label>
              <input
                value={performedBy}
                onChange={e => setPerformedBy(e.target.value)}
                placeholder="Manager name"
                className="w-full rounded-xl border border-slate-200 p-3 text-sm"
              />
            </div>
          </div>

          <button
            disabled={loading || !findings.trim() || !resolution.trim()}
            onClick={onSave}
            className="w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save Investigation"}
          </button>
        </div>

        <div className="mt-8 border-t pt-6">
          <div className="mb-4 flex items-center gap-2">
            <History size={19} />
            <h3 className="font-bold">Investigation Event History</h3>
          </div>

          {events.length === 0 ? (
            <p className="text-sm text-slate-500">
              No event history available.
            </p>
          ) : (
            <div className="space-y-3">
              {events.map((event, index) => (
                <div key={event.id || index} className="rounded-xl bg-slate-50 p-4">
                  <div className="flex flex-wrap justify-between gap-2">
                    <span className="text-sm font-semibold">
                      {event.event_type || "Investigation Event"}
                    </span>
                    <span className="text-xs text-slate-500">
                      {event.event_at
                        ? new Date(event.event_at).toLocaleString()
                        : ""}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    {event.description || "—"}
                  </p>
                  {event.performed_by && (
                    <p className="mt-2 text-xs text-slate-500">
                      By: {event.performed_by}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InventoryLookup() {
  const [storeId, setStoreId] = useState("");
  const [skuId, setSkuId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function lookup(event) {
    event.preventDefault();
    if (!storeId || !skuId || Number(storeId) <= 0 || Number(skuId) <= 0) {
      setError("Enter valid positive Store ID and SKU ID values.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await api.get("/inventory/lookup", {
        params: { store_id: Number(storeId), sku_id: Number(skuId) },
      });
      setResult(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-slate-900">Inventory Position Lookup</h3>
        <p className="mb-5 mt-1 text-sm text-slate-500">Read the calculated expected stock and latest cycle count for a store/SKU pair.</p>
        <form onSubmit={lookup} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <label className="text-sm font-medium text-slate-700">Store ID<input type="number" min="1" value={storeId} onChange={(event) => setStoreId(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5" placeholder="e.g. 1" /></label>
          <label className="text-sm font-medium text-slate-700">SKU ID<input type="number" min="1" value={skuId} onChange={(event) => setSkuId(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5" placeholder="e.g. 1" /></label>
          <div className="flex items-end"><button disabled={loading} className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{loading ? "Looking up..." : "Check Inventory"}</button></div>
        </form>
      </section>
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
      {result && <section className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Store</p><p className="mt-2 text-xl font-bold">{result.store_code || result.store_id}</p></div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">SKU</p><p className="mt-2 text-xl font-bold">{result.sku_code || result.sku_id}</p></div>
        <div className="rounded-2xl border border-blue-100 bg-blue-50 p-5 shadow-sm sm:col-span-2"><p className="text-sm text-blue-700">Expected stock</p><p className="mt-2 text-3xl font-bold text-blue-900">{result.expected_stock}</p></div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:col-span-2"><p className="font-semibold">Latest cycle count</p>{result.latest_cycle_count ? <div className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3"><div><p className="text-slate-500">Count code</p><p className="mt-1 font-semibold">{result.latest_cycle_count.count_code}</p></div><div><p className="text-slate-500">Counted quantity</p><p className="mt-1 font-semibold">{result.latest_cycle_count.counted_quantity}</p></div><div><p className="text-slate-500">Counted at</p><p className="mt-1 font-semibold">{result.latest_cycle_count.counted_at ? new Date(result.latest_cycle_count.counted_at).toLocaleString() : "—"}</p></div></div> : <p className="mt-2 text-sm text-slate-500">No cycle count recorded for this store/SKU pair.</p>}</div>
      </section>}
    </div>
  );
}

function ModelPerformance() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api.get("/metrics/model").then((response) => { if (active) setMetrics(response.data); }).catch((err) => { if (active) setError(getErrorMessage(err)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  if (loading) return <div className="rounded-xl border bg-white p-10 text-center text-slate-500">Loading model metrics...</div>;
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>;
  const models = metrics?.models || [];
  const metricKeys = ["precision", "recall", "f1_score", "accuracy", "false_positive_rate"];
  return <div className="space-y-5">
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><strong>Synthetic-data evaluation:</strong> {metrics?.disclaimer || "These results are based on synthetic data and do not establish real-world production accuracy."}</div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Records evaluated</p><p className="mt-2 text-3xl font-bold">{metrics?.records_evaluated ?? "—"}</p></div>
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Actual shrinkage cases</p><p className="mt-2 text-3xl font-bold">{metrics?.actual_shrinkage_cases ?? "—"}</p></div>
    </div>
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">{models.map((model) => <section key={model.model} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h3 className="text-lg font-bold">{model.model}</h3><div className="mt-5 grid grid-cols-2 gap-4">{metricKeys.map((key) => <div key={key} className="rounded-xl bg-slate-50 p-4"><p className="text-xs uppercase text-slate-500">{key.replaceAll("_", " ")}</p><p className="mt-2 text-2xl font-bold">{model[key] ?? "—"}</p></div>)}</div><p className="mt-4 text-xs text-slate-500">Evaluation: {model.evaluation || "Not specified"}</p></section>)}</div>
    {models.length === 0 && <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">No model metrics file is available. The application will not regenerate data automatically.</div>}
  </div>;
}

function SystemHealth() {
  const [checks, setChecks] = useState({ api: null, database: null });
  const [loading, setLoading] = useState(true);
  const [checkedAt, setCheckedAt] = useState(null);
  async function refresh() {
    setLoading(true);
    const [apiResult, databaseResult] = await Promise.allSettled([
      api.get("/health"),
      api.get("/health/database"),
    ]);
    setChecks({
      api: apiResult.status === "fulfilled" ? apiResult.value.data : { status: "error" },
      database: databaseResult.status === "fulfilled" ? databaseResult.value.data : { status: "error" },
    });
    setCheckedAt(new Date());
    setLoading(false);
  }
  useEffect(() => {
    let active = true;
    async function initialCheck() {
      const [apiResult, databaseResult] = await Promise.allSettled([
        api.get("/health"),
        api.get("/health/database"),
      ]);
      if (!active) return;
      setChecks({
        api: apiResult.status === "fulfilled" ? apiResult.value.data : { status: "error" },
        database: databaseResult.status === "fulfilled" ? databaseResult.value.data : { status: "error" },
      });
      setCheckedAt(new Date());
      setLoading(false);
    }
    initialCheck();
    return () => { active = false; };
  }, []);
  const healthy = checks.api?.status === "healthy" && checks.database?.status === "connected";
  return <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="font-bold">System Connectivity</h3><p className="mt-1 text-sm text-slate-500">Read-only API and database health checks</p></div><button onClick={refresh} disabled={loading} className="rounded-lg border px-4 py-2 text-sm font-semibold disabled:opacity-50">{loading ? "Checking..." : "Refresh checks"}</button></div>
    <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">{[{ label: "FastAPI service", value: checks.api?.status || "Checking" }, { label: "MySQL database", value: checks.database?.status || "Checking" }].map((item) => <div key={item.label} className="rounded-xl bg-slate-50 p-5"><p className="text-sm text-slate-500">{item.label}</p><p className={`mt-2 text-xl font-bold ${item.value === "healthy" || item.value === "connected" ? "text-emerald-600" : item.value === "error" ? "text-red-600" : "text-slate-700"}`}>{item.value}</p></div>)}</div>
    <p className="mt-5 text-xs text-slate-500">Last checked: {checkedAt ? checkedAt.toLocaleString() : "—"}</p>
    {healthy && <p className="mt-3 text-sm font-medium text-emerald-700">All configured health checks are passing.</p>}
  </section>;
}

function SkuCatalog({ items, total, page, search, onSearch, onPage }) {
  const pageSize = 20;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-bold text-slate-900">Product Catalog</h3>
          <p className="mt-1 text-xs text-slate-500">SKU master data and unit pricing</p>
        </div>
        <div className="relative w-full sm:max-w-sm">
          <Search className="absolute left-3 top-3 text-slate-400" size={17} />
          <input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="Search SKU or product name" className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500" />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr>{["SKU Code", "Product", "Category", "Unit Cost", "Unit Price", "Active"].map((heading) => <th key={heading} className="whitespace-nowrap px-5 py-4">{heading}</th>)}</tr></thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((sku) => <tr key={sku.id} className="hover:bg-slate-50"><td className="px-5 py-4 font-semibold">{sku.sku_code}</td><td className="px-5 py-4">{sku.name}</td><td className="px-5 py-4">{sku.category}</td><td className="px-5 py-4">{sku.unit_cost}</td><td className="px-5 py-4">{sku.unit_price}</td><td className="px-5 py-4">{sku.is_active ? "Yes" : "No"}</td></tr>)}
            {items.length === 0 && <tr><td colSpan="6" className="p-8 text-center text-slate-500">No products found.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm">
        <span className="text-slate-500">{total} products · Page {page} of {pages}</span>
        <div className="flex gap-2"><button disabled={page <= 1} onClick={() => onPage(page - 1)} className="rounded-lg border px-3 py-1 disabled:opacity-40">Previous</button><button disabled={page >= pages} onClick={() => onPage(page + 1)} className="rounded-lg border px-3 py-1 disabled:opacity-40">Next</button></div>
      </div>
    </section>
  );
}

function Analytics({ data }) {
  const severityData = data?.alerts_by_severity || [];
  const statusData = data?.alerts_by_status || [];
  const storeData = data?.alerts_by_store || [];
  const maxSeverity = Math.max(...severityData.map((item) => item.value), 1);
  const maxStore = Math.max(...storeData.map((item) => item.value), 1);
  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold">Alert Severity Distribution</h3><p className="mb-7 mt-1 text-xs text-slate-500">Live aggregate from all stored alerts</p>
        <div className="space-y-6">{severityData.map((item) => { const color = { HIGH: "bg-red-500", MEDIUM: "bg-amber-500", LOW: "bg-emerald-500" }[item.name] || "bg-blue-500"; return <div key={item.name}><div className="mb-2 flex justify-between text-sm"><span className="font-medium">{item.name}</span><span className="font-bold">{item.value}</span></div><div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${color}`} style={{ width: `${(item.value / maxSeverity) * 100}%` }} /></div></div>; })}{severityData.length === 0 && <p className="text-sm text-slate-500">No severity data available.</p>}</div>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold">Alert Status Overview</h3><p className="mb-5 mt-1 text-xs text-slate-500">Current workflow status across all alerts</p>
        <div className="space-y-3">{statusData.map((item) => <div key={item.name} className="flex items-center justify-between rounded-xl bg-slate-50 p-4"><span className="text-sm font-medium">{item.name}</span><span className="text-lg font-bold">{item.value}</span></div>)}{statusData.length === 0 && <p className="text-sm text-slate-500">No status data available.</p>}</div>
      </section>
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm xl:col-span-2">
        <h3 className="font-bold">Stores with Most Shrinkage Alerts</h3><p className="mb-5 mt-1 text-xs text-slate-500">Top ten stores by alert volume</p>
        <div className="space-y-4">{storeData.map((item) => <div key={item.store_id}><div className="mb-1 flex justify-between gap-3 text-sm"><span className="truncate">{item.store_code} · {item.name}</span><strong>{item.value}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-600" style={{ width: `${(item.value / maxStore) * 100}%` }} /></div></div>)}{storeData.length === 0 && <p className="text-sm text-slate-500">No store-level alert data available.</p>}</div>
      </section>
    </div>
  );
}
