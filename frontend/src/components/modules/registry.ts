import type { LucideIcon } from "lucide-react";
import {
  ArrowLeftRight,
  BookOpen,
  Building2,
  Clock,
  LayoutGrid,
  MonitorSmartphone,
  Package,
  Receipt,
  ShoppingBag,
  Store,
  Truck,
  Users,
  Wallet,
  Warehouse,
} from "lucide-react";

export type ModuleDef = {
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  actionLabel?: string;
  icon: LucideIcon;
};

export const modules = {
  sales: {
    title: "Sales",
    description: "Record and review store sales.",
    emptyTitle: "No sales yet",
    emptyDescription: "When you complete a sale, it will appear here with payment, tax and profit.",
    actionLabel: "New sale",
    icon: ShoppingBag,
  },
  "sale-returns": {
    title: "Sales Returns",
    description: "Process customer refunds and track items returned to your store.",
    emptyTitle: "No returns yet",
    emptyDescription: "When you process a refund, it will appear here so you can keep track of every return.",
    actionLabel: "New return",
    icon: Receipt,
  },
  customers: {
    title: "Customers",
    description: "Keep a customer list and record who bought what.",
    emptyTitle: "No customers yet",
    emptyDescription: "Add a customer to track sales on account, contact details and outstanding balances.",
    actionLabel: "Add customer",
    icon: Users,
  },
  pos: {
    title: "Point of Sale",
    description: "Take payments at the counter with barcode, cash and mobile money.",
    emptyTitle: "POS is not live yet",
    emptyDescription: "The register, barcode mode and receipt printer connect in the POS phase. Settings already store hardware preferences on this computer.",
    icon: MonitorSmartphone,
  },
  shifts: {
    title: "Shifts",
    description: "Open and close cashier shifts, cash and variance.",
    emptyTitle: "No shifts yet",
    emptyDescription: "Shifts will list who opened, cash counted and whether the till was over or short.",
    actionLabel: "Open shift",
    icon: Clock,
  },
  purchases: {
    title: "Purchases",
    description: "Supplier spend, purchase orders and receiving.",
    emptyTitle: "No purchases yet",
    emptyDescription: "Create a purchase when stock arrives so inventory and accounts stay in step.",
    actionLabel: "New purchase",
    icon: Truck,
  },
  "purchase-returns": {
    title: "Purchase Returns",
    description: "Return goods to suppliers and reverse received stock.",
    emptyTitle: "No purchase returns yet",
    emptyDescription: "Returns to suppliers will show here after purchasing is enabled.",
    actionLabel: "New return",
    icon: Receipt,
  },
  suppliers: {
    title: "Suppliers",
    description: "People and companies you buy from.",
    emptyTitle: "No suppliers yet",
    emptyDescription: "Add a supplier to raise purchase orders and track what you owe.",
    actionLabel: "Add supplier",
    icon: Building2,
  },
  products: {
    title: "Products",
    description: "Catalogue, prices, barcodes and tax classes.",
    emptyTitle: "No products yet",
    emptyDescription: "Add items before you can sell, count stock or transfer between centres.",
    actionLabel: "New product",
    icon: Package,
  },
  inventory: {
    title: "Stock Levels",
    description: "On-hand quantity at each storage centre.",
    emptyTitle: "No stock to show",
    emptyDescription: "Stock levels appear after products exist and receiving or opening balances are posted.",
    icon: LayoutGrid,
  },
  "stock-transfer": {
    title: "Stock Transfer",
    description: "Move stock between the places this store keeps it.",
    emptyTitle: "No transfers yet",
    emptyDescription: "Transfers will list source, destination and quantities once inventory is live.",
    actionLabel: "New transfer",
    icon: ArrowLeftRight,
  },
  "storage-centers": {
    title: "Storage Centers",
    description: "Warehouses, back rooms and other places this store keeps stock.",
    emptyTitle: "No storage centres yet",
    emptyDescription: "Add a centre so you can count stock and transfer between locations.",
    actionLabel: "New storage centre",
    icon: Warehouse,
  },
  "storage-transfers": {
    title: "Storage Center Transfers",
    description: "Move stock between the places this store keeps it.",
    emptyTitle: "Add a second storage centre",
    emptyDescription: "Add a second storage centre to move stock between centres.",
    icon: ArrowLeftRight,
  },
  sections: {
    title: "Sections",
    description: "Parts of your shop, like Bakery or Butchery. Put items in sections, then run the Sales or Profit Report for one section.",
    emptyTitle: "No sections yet. Add one with New section.",
    emptyDescription: "Items in no section: 0",
    actionLabel: "New section",
    icon: Store,
  },
  expenses: {
    title: "Expenses",
    description: "Track operating costs and overhead.",
    emptyTitle: "No expenses recorded",
    emptyDescription: "Start logging your store’s operating costs and overhead to keep an accurate picture of profitability.",
    actionLabel: "New expense",
    icon: Wallet,
  },
  accounting: {
    title: "Accounting",
    description: "Chart of accounts, journals and period close.",
    emptyTitle: "Ledgers are not open yet",
    emptyDescription: "Double-entry posting ships in a later phase. Status colours for paid, pending and failed will apply here too.",
    icon: BookOpen,
  },
} as const satisfies Record<string, ModuleDef>;

export type ModuleSlug = keyof typeof modules;
