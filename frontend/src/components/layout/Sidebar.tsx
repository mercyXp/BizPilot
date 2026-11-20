"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { isNavActive, navGroups, settingsItem, type NavItem } from "@/lib/nav";
import { cn } from "@/lib/cn";
import { Logo, LogoMark } from "@/components/ui/logo";
import { navIcons } from "@/components/layout/NavIcons";

function NavLink({
  item,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const active = isNavActive(pathname, item.href);
  const Icon = navIcons[item.icon];

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
      className={cn(
        "relative flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium",
        "transition-colors duration-standard ease-entrance",
        active
          ? "bg-brand-soft text-brand-deep"
          : "text-secondary hover:bg-muted-bg hover:text-ink",
      )}
    >
      {active ? (
        <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-brand" />
      ) : null}
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      <span className={cn("truncate", collapsed && "sr-only")}>{item.label}</span>
    </Link>
  );
}

export function Sidebar({
  orgName,
  collapsed,
  onToggle,
  onNavigate,
  className,
}: {
  orgName: string;
  collapsed: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-border bg-surface",
        "transition-[width] duration-sidebar ease-entrance",
        collapsed ? "w-[72px]" : "w-[248px]",
        className,
      )}
    >
      <div className={cn("flex items-center gap-2 border-b border-border px-3 py-3", collapsed && "justify-center px-2")}>
        <Link href="/app" className="block min-w-0" aria-label="BizPilot home">
          {collapsed ? <LogoMark size={32} /> : <Logo height={28} />}
        </Link>
      </div>
      <div className={cn("border-b border-border px-3 py-2.5", collapsed && "px-2")}>
        <p className={cn("truncate text-xs font-medium text-secondary", collapsed && "sr-only")}>
          {orgName}
        </p>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3" aria-label="Store navigation">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-3">
            <p
              className={cn(
                "mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted",
                collapsed && "sr-only",
              )}
            >
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavLink key={item.href} item={item} collapsed={collapsed} onNavigate={onNavigate} />
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="border-t border-border p-2">
        <NavLink item={settingsItem} collapsed={collapsed} onNavigate={onNavigate} />
        <button
          type="button"
          onClick={onToggle}
          className="btn-press mt-1 flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-[13px] text-secondary hover:bg-muted-bg hover:text-ink"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          <span className={cn(collapsed && "sr-only")}>Collapse</span>
        </button>
      </div>
    </aside>
  );
}
