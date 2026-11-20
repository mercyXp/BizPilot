export type NavItem = {
  href: string;
  label: string;
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
      { href: "/app/sales", label: "Sales", icon: "sales" },
      { href: "/app/sales/returns", label: "Sale Returns", icon: "returns" },
      { href: "/app/customers", label: "Customers", icon: "customers" },
      { href: "/app/pos", label: "Point of Sale", icon: "pos" },
      { href: "/app/shifts", label: "Shifts", icon: "shifts" },
    ],
  },
  {
    label: "Purchases",
    items: [
      { href: "/app/purchases", label: "Purchases", icon: "purchases" },
      { href: "/app/purchases/returns", label: "Purchase Returns", icon: "purchaseReturns" },
      { href: "/app/suppliers", label: "Suppliers", icon: "suppliers" },
    ],
  },
  {
    label: "Inventory",
    items: [
      { href: "/app/products", label: "Products", icon: "products" },
      { href: "/app/inventory", label: "Stock Levels", icon: "stock" },
      { href: "/app/inventory/transfers", label: "Stock Transfer", icon: "transfer" },
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
    items: [{ href: "/app/expenses", label: "Expenses", icon: "expenses" }],
  },
  {
    label: "Store Assistants",
    items: [{ href: "/app/assistants", label: "Store Assistants", icon: "assistants" }],
  },
  {
    label: "Store Reports",
    items: [
      { href: "/app/reports", label: "Reports", icon: "reports" },
      { href: "/app/accounting", label: "Accounting", icon: "accounting" },
    ],
  },
  {
    label: "BizPilot AI",
    items: [{ href: "/app/assistant", label: "Assistant", icon: "assistant" }],
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
