import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { LayoutDashboard, History, Bookmark, Database, Settings } from "lucide-react";
import { useQueryHistory } from "@/hooks/use-query";

export default function Sidebar() {
  const [location] = useLocation();
  const { history } = useQueryHistory();
  
  const isActive = (path: string) => location === path;
  
  return (
    <aside className="w-64 hidden md:block bg-white border-r border-gray-200 overflow-y-auto">
      <div className="px-4 py-5 sm:p-6">
        <nav className="space-y-1" aria-label="Sidebar">
          <Link href="/">
            <a
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive("/")
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
              aria-current={isActive("/") ? "page" : undefined}
            >
              <LayoutDashboard className={cn(
                "mr-3 h-5 w-5",
                isActive("/") ? "text-primary-500" : "text-gray-400"
              )} />
              <span className="truncate">Dashboard</span>
            </a>
          </Link>

          <Link href="/query-history">
            <a
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive("/query-history")
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <History className={cn(
                "mr-3 h-5 w-5",
                isActive("/query-history") ? "text-primary-500" : "text-gray-400"
              )} />
              <span className="truncate">Query History</span>
            </a>
          </Link>

          <Link href="/saved-queries">
            <a
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive("/saved-queries")
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Bookmark className={cn(
                "mr-3 h-5 w-5",
                isActive("/saved-queries") ? "text-primary-500" : "text-gray-400"
              )} />
              <span className="truncate">Saved Queries</span>
            </a>
          </Link>

          <Link href="/database-schema">
            <a
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive("/database-schema")
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Database className={cn(
                "mr-3 h-5 w-5",
                isActive("/database-schema") ? "text-primary-500" : "text-gray-400"
              )} />
              <span className="truncate">Database Schema</span>
            </a>
          </Link>

          <Link href="/settings">
            <a
              className={cn(
                "flex items-center px-3 py-2 text-sm font-medium rounded-md",
                isActive("/settings")
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Settings className={cn(
                "mr-3 h-5 w-5",
                isActive("/settings") ? "text-primary-500" : "text-gray-400"
              )} />
              <span className="truncate">Settings</span>
            </a>
          </Link>
        </nav>
      </div>

      {/* Recent Queries Section */}
      <div className="px-4 pt-4 pb-6">
        <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Recent Queries
        </h2>
        <ul className="mt-3 space-y-2">
          {history?.slice(0, 5).map((query) => (
            <li key={query.id}>
              <Link href={`/query-history/${query.id}`}>
                <a className="block text-sm text-gray-600 hover:text-primary-600 truncate">
                  {query.naturalLanguageQuery}
                </a>
              </Link>
            </li>
          ))}
          {!history && Array(3).fill(0).map((_, i) => (
            <li key={i} className="h-5 bg-gray-100 animate-pulse rounded"></li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
