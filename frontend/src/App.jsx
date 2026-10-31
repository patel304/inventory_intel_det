
import { useEffect, useState } from "react";
import {
  LayoutDashboard, AlertTriangle, ClipboardList,
  BarChart3, Search, Bell, Package, ShieldCheck,
  TrendingDown, Menu, X, History, Plus, RefreshCw
} from "lucide-react";
import api from "./services/api";

const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Shrinkage Alerts", icon: AlertTriangle },
  { name: "Investigations", icon: ClipboardList },
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
  const [investigations, setInvestigations] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);
  const [events, setEvents] = useState([]);

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
    const response = await api.get("/alerts");
    setAlerts(getList(response.data));
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
        if (
          page === "Dashboard" ||
          page === "Shrinkage Alerts" ||
          page === "Analytics"
        ) {
          await fetchAlerts();
        }

        if (page === "Investigations") {
          await fetchInvestigations();
        }
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Unable to load data. Check backend connection."
        );
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [page]);

  const openCount = alerts.filter(a => a.status === "OPEN").length;
  const highCount = alerts.filter(a => a.severity === "HIGH").length;

  const filteredAlerts = alerts.filter(alert => {
    const search = searchTerm.toLowerCase();

    const matchesSearch =
      String(alert.alert_code || "").toLowerCase().includes(search) ||
      String(alert.store_id || "").includes(search) ||
      String(alert.sku_id || "").includes(search);

    const matchesSeverity =
      severityFilter === "ALL" ||
      alert.severity === severityFilter;

    const matchesStatus =
      statusFilter === "ALL" ||
      alert.status === statusFilter;

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const severityData = ["HIGH", "MEDIUM", "LOW"].map(name => ({
    name,
    value: alerts.filter(a => a.severity === name).length,
  }));

  const statusData = [
    "OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"
  ].map(name => ({
    name,
    value: alerts.filter(a => a.status === name).length,
  }));

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
              {(page === "Dashboard" || page === "Analytics") && (
                <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <StatCard title="Total Alerts" value={alerts.length} icon={AlertTriangle} color="blue" />
                  <StatCard title="Open Alerts" value={openCount} icon={ClipboardList} color="amber" />
                  <StatCard title="High Severity" value={highCount} icon={TrendingDown} color="red" />
                  <StatCard title="Detection Engine" value="Active" icon={ShieldCheck} color="green" />
                </div>
              )}

              {(page === "Dashboard" || page === "Shrinkage Alerts") && (
                <AlertTable
                  alerts={
                    page === "Dashboard"
                      ? filteredAlerts.slice(0, 10)
                      : filteredAlerts
                  }
                  onSelect={setSelectedAlert}
                  searchTerm={searchTerm}
                  setSearchTerm={setSearchTerm}
                  severityFilter={severityFilter}
                  setSeverityFilter={setSeverityFilter}
                  statusFilter={statusFilter}
                  setStatusFilter={setStatusFilter}
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
                <Analytics
                  severityData={severityData}
                  statusData={statusData}
                />
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

function StatCard({ title, value, icon: Icon, color }) {
  const styles = {
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    red: "bg-red-50 text-red-600",
    green: "bg-emerald-50 text-emerald-600",
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <div className={`rounded-xl p-3 ${styles[color]}`}>
          <Icon size={21} />
        </div>
      </div>
      <h3 className="mt-5 text-3xl font-bold text-slate-900">
        {value}
      </h3>
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
            Showing {alerts.length} alerts
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
                <td className="px-5 py-4">{alert.store_id}</td>
                <td className="px-5 py-4">{alert.sku_id}</td>
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
    ["Estimated Loss", alert.estimated_loss],
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

function Analytics({ severityData, statusData }) {
  const max = Math.max(...severityData.map(x => x.value), 1);

  return (
    <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <h3 className="font-bold">Alert Severity Distribution</h3>
        <p className="mb-7 mt-1 text-xs text-slate-500">
          Breakdown by severity level
        </p>
        <div className="space-y-6">
          {severityData.map(item => {
            const colors = {
              HIGH: "bg-red-500",
              MEDIUM: "bg-amber-500",
              LOW: "bg-emerald-500",
            };
            return (
              <div key={item.name}>
                <div className="mb-2 flex justify-between text-sm">
                  <span className="font-medium">{item.name}</span>
                  <span className="font-bold">{item.value}</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${colors[item.name]}`}
                    style={{ width: `${(item.value / max) * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <h3 className="font-bold">Alert Status Overview</h3>
        <p className="mb-7 mt-1 text-xs text-slate-500">
          Current alert workflow status
        </p>
        <div className="space-y-4">
          {statusData.map(item => (
            <div key={item.name} className="flex items-center justify-between rounded-xl bg-slate-50 p-4">
              <span className="text-sm font-medium">{item.name}</span>
              <span className="text-lg font-bold">{item.value}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
