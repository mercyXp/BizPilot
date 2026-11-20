"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Bell, Menu, Moon, Sun, X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { drawerVariants, overlayVariants } from "@/lib/motion";
import { cn } from "@/lib/cn";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "B";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading, currentOrg, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/sign-in");
    }
  }, [loading, user, router]);

  useEffect(() => {
    setMobileOpen(false);
    setMenuOpen(false);
  }, [pathname]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen">
        <div className="hidden w-[248px] border-r border-border bg-surface p-4 md:block">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="mt-6 h-4 w-20" />
          <Skeleton className="mt-3 h-8 w-full" />
          <Skeleton className="mt-2 h-8 w-full" />
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="mt-6 h-28 w-full" />
        </div>
      </div>
    );
  }

  const orgName = currentOrg?.name ?? "No organization";

  return (
    <div className="flex min-h-screen bg-canvas text-ink">
      <div className="hidden md:block">
        <div className="sticky top-0 h-screen">
          <Sidebar
            orgName={orgName}
            collapsed={collapsed}
            onToggle={() => setCollapsed((value) => !value)}
          />
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen ? (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-ink/30 md:hidden"
              variants={overlayVariants}
              initial="hidden"
              animate="show"
              exit="exit"
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              className="fixed inset-y-0 left-0 z-50 md:hidden"
              variants={drawerVariants}
              initial="hidden"
              animate="show"
              exit="exit"
            >
              <Sidebar
                orgName={orgName}
                collapsed={false}
                onToggle={() => setMobileOpen(false)}
                onNavigate={() => setMobileOpen(false)}
              />
            </motion.div>
          </>
        ) : null}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-border bg-surface/90 px-4 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-press rounded-md p-2 text-secondary hover:bg-muted-bg md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
            <p className="truncate text-sm font-medium text-ink">{orgName}</p>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="hidden items-center gap-1 rounded-md px-2 py-1 text-xs text-muted sm:inline-flex"
              title="Light theme is the BizPilot default"
            >
              <Sun className="h-3.5 w-3.5 text-brand" />
              <Moon className="h-3.5 w-3.5 opacity-30" />
            </span>
            <button
              type="button"
              className="btn-press rounded-md p-2 text-secondary hover:bg-muted-bg"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
            </button>
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((value) => !value)}
                className="btn-press flex h-8 w-8 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand-deep"
                aria-expanded={menuOpen}
                aria-label="Account menu"
              >
                {initials(user.full_name || user.email)}
              </button>
              <AnimatePresence>
                {menuOpen ? (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                    className="absolute right-0 mt-2 w-56 rounded-lg border border-border bg-surface p-1 shadow-lift"
                  >
                    <p className="truncate px-3 py-2 text-xs text-secondary">{user.email}</p>
                    <Button href="/app/settings" variant="ghost" className="w-full justify-start">
                      Settings
                    </Button>
                    <button
                      type="button"
                      className="btn-press w-full rounded-md px-3 py-2 text-left text-sm text-danger hover:bg-danger-bg"
                      onClick={() => {
                        void logout().then(() => router.push("/sign-in"));
                      }}
                    >
                      Sign out
                    </button>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>
          </div>
        </header>
        <main className={cn("app-grid-bg flex-1 px-4 py-6 sm:px-6 lg:px-8")}>{children}</main>
      </div>
    </div>
  );
}
