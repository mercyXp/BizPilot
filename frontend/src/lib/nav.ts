export type NavItem = {
  href: string;
  label: string;
  permission?: string;
  icon:
    | "home"
    | "sales"
    | "returns"
    | "customers"
    | "pos"
    | "shifts"
    | "purchases"
    | "purchaseReturns"
    | "suppliers"
    | "products"
    | "stock"
    | "transfer"
    | "warehouse"
    | "warehouseTransfer"
    | "sections"
    | "expenses"
    | "assistants"
    | "reports"
    | "accounting"
    | "assistant"
    | "zra"
    | "integrations"
    | "settings";
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

/** Information architecture matches the store-operations screenshots. */
export const navGroups: NavGroup[] = [
  {
    label: "Store Dashboard",
    items: [{ href: "/app", label: "Home", icon: "home" }],
  },
  {
    label: "Sales",
    items: [
      { href: "/app/sales", label: "Sales", icon: "sales", permission: "sales.view" },
      { href: "/app/sales/returns", label: "Sale Returns", icon: "returns", permission: "sales.view" },
      { href: "/app/customers", label: "Customers", icon: "customers", permission: "customers.manage" },
      { href: "/app/pos", label: "Point of Sale", icon: "pos", permission: "pos.session.open" },
      { href: "/app/shifts", label: "Shifts", icon: "shifts", permission: "pos.session.open" },
    ],
  },
  {
    label: "Purchases",
    items: [
      { href: "/app/purchases", label: "Purchases", icon: "purchases", permission: "purchases.view" },
      { href: "/app/purchases/returns", label: "Purchase Returns", icon: "purchaseReturns", permission: "purchases.view" },
      { href: "/app/suppliers", label: "Suppliers", icon: "suppliers", permission: "purchases.view" },
    ],
  },
  {
    label: "Inventory",
    items: [
      { href: "/app/products", label: "Products", icon: "products", permission: "catalogue.view" },
      { href: "/app/inventory", label: "Stock Levels", icon: "stock", permission: "inventory.view" },
      { href: "/app/inventory/transfers", label: "Stock Transfer", icon: "transfer", permission: "inventory.transfer" },
      { href: "/app/storage-centers", label: "Storage Centers", icon: "warehouse" },
      {
        href: "/app/storage-centers/transfers",
        label: "Storage Center Transfers",
        icon: "warehouseTransfer",
      },
      { href: "/app/sections", label: "Sections", icon: "sections" },
    ],
  },
  {
    label: "Expenses",
    items: [{ href: "/app/expenses", label: "Expenses", icon: "expenses", permission: "expenses.create" }],
  },
  {
    label: "Store Assistants",
    items: [{ href: "/app/assistants", label: "Store Assistants", icon: "assistants", permission: "users.manage" }],
  },
  {
    label: "Store Reports",
    items: [
      { href: "/app/reports", label: "Reports", icon: "reports", permission: "reports.view" },
      { href: "/app/accounting", label: "Accounting", icon: "accounting", permission: "accounting.reports.view" },
      { href: "/app/audit", label: "Audit trail", icon: "accounting", permission: "accounting.reports.view" },
    ],
  },
  {
    label: "BizPilot AI",
    items: [{ href: "/app/assistant", label: "Assistant", icon: "assistant", permission: "ai.use" }],
  },
  {
    label: "Compliance",
    items: [
      { href: "/app/zra", label: "ZRA Smart Invoice", icon: "zra" },
      { href: "/app/integrations", label: "Integrations", icon: "integrations" },
    ],
  },
];

export const settingsItem: NavItem = {
  href: "/app/settings",
  label: "Settings",
  icon: "settings",
};

export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/app") return pathname === "/app";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function canSeeNavItem(item: NavItem, permissions: string[] | null): boolean {
  if (!item.permission) return true;
  if (permissions === null) return true;
  return permissions.includes(item.permission);
}
