// Sidebar — left navigation between the 9 pages.
import { NavLink } from "react-router-dom";
import {
  BedDouble, CalendarDays, FileText, LayoutDashboard, MessageSquare, Pill, Receipt, Settings, Users,
} from "lucide-react";

export const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/chat", label: "AI Chat", icon: MessageSquare },
  { to: "/beds", label: "Beds", icon: BedDouble },
  { to: "/patients", label: "Patients", icon: Users },
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/pharmacy", label: "Pharmacy", icon: Pill },
  { to: "/billing", label: "Billing", icon: Receipt },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <nav className="flex shrink-0 flex-row gap-1 overflow-x-auto border-b border-line bg-surface p-2 md:w-60 md:flex-col md:border-b-0 md:border-r md:p-4"
         aria-label="Main">
      <div className="mb-6 hidden items-center gap-2 px-2 md:flex">
        <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
          <rect width="32" height="32" rx="8" fill="#0F766E" />
          <path d="M13 8h6v5h5v6h-5v5h-6v-5H8v-6h5z" fill="white" />
        </svg>
        <span className="font-display text-lg font-bold">HospitalOS</span>
      </div>
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === "/"}
          className={({ isActive }) =>
            `flex items-center gap-3 whitespace-nowrap rounded-control px-3 py-2 text-sm font-medium transition-colors ${
              isActive ? "bg-primary-soft text-primary" : "text-ink-muted hover:bg-canvas hover:text-ink"}`}>
          <Icon size={17} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
      <p className="mt-auto hidden px-2 pt-6 text-xs text-ink-subtle md:block">Synthetic data only · College PBL</p>
    </nav>
  );
}
