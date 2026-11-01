import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import api, { getErrorMessage, getList } from "../services/api";
import { EmptyState, ErrorBanner, LoadingState } from "../components/Feedback";

export default function Stores() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const handle = setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const response = await api.get("/stores", {
          params: { page, page_size: 20, search: search || undefined },
        });
        setItems(getList(response.data));
        setTotal(response.data.total ?? getList(response.data).length);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [page, search]);

  return (
    <>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-3 text-slate-400" size={17} />
          <input
            value={search}
            onChange={(event) => {
              setPage(1);
              setSearch(event.target.value);
            }}
            placeholder="Search store code, name or city"
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500"
          />
        </div>
        <p className="text-sm text-slate-500">{total} stores</p>
      </div>
      <ErrorBanner message={error} />
      {loading ? (
        <LoadingState />
      ) : items.length === 0 ? (
        <EmptyState title="No stores found" detail="Try a different search." />
      ) : (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  {["Code", "Name", "City", "State", "Active"].map((heading) => (
                    <th key={heading} className="px-5 py-4">{heading}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((store) => (
                  <tr key={store.id}>
                    <td className="px-5 py-4 font-semibold">{store.store_code}</td>
                    <td className="px-5 py-4">{store.name}</td>
                    <td className="px-5 py-4">{store.city}</td>
                    <td className="px-5 py-4">{store.state}</td>
                    <td className="px-5 py-4">{store.is_active ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} total={total} pageSize={20} onChange={setPage} />
        </section>
      )}
    </>
  );
}

export function Pagination({ page, total, pageSize, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
        className="rounded-lg border px-3 py-1 disabled:opacity-40"
      >
        Previous
      </button>
      <span className="text-slate-500">Page {page} of {pages}</span>
      <button
        type="button"
        disabled={page >= pages}
        onClick={() => onChange(page + 1)}
        className="rounded-lg border px-3 py-1 disabled:opacity-40"
      >
        Next
      </button>
    </div>
  );
}
