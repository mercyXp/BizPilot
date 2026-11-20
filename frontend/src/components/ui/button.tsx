import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

const variants = {
  primary:
    "bg-brand text-white shadow-sm hover:bg-brand-deep hover:shadow-lift disabled:bg-brand/50",
  secondary:
    "bg-brand-soft text-brand-deep hover:bg-brand-soft/80 disabled:opacity-50",
  outline:
    "border border-border bg-surface text-ink hover:border-brand/40 hover:bg-canvas disabled:opacity-50",
  ghost: "text-secondary hover:bg-muted-bg hover:text-ink disabled:opacity-50",
  danger: "bg-danger text-white hover:bg-danger/90 disabled:opacity-50",
} as const;

const sizes = {
  sm: "h-8 px-3 text-xs",
  md: "h-9 px-3.5 text-sm",
  lg: "h-11 px-5 text-sm",
} as const;

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  href?: string;
  icon?: ReactNode;
  arrow?: boolean;
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  href,
  icon,
  arrow,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  const classes = cn(
    "btn-press group inline-flex items-center justify-center gap-2 rounded-md font-medium",
    "disabled:pointer-events-none disabled:cursor-not-allowed",
    variants[variant],
    sizes[size],
    className,
  );

  const content = (
    <>
      {icon}
      {children}
      {arrow ? (
        <span aria-hidden className="inline-block transition-transform duration-standard ease-entrance group-hover:translate-x-0.5">
          →
        </span>
      ) : null}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  }

  return (
    <button type={type} className={classes} {...props}>
      {content}
    </button>
  );
}
