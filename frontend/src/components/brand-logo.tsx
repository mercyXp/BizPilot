import Link from "next/link";

export function BrandLogo() {
  return (
    <Link href="/" className="flex items-center gap-2" aria-label="BizPilot home">
      <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0" aria-hidden>
        <circle cx="16" cy="16" r="15" fill="#0F766E" />
        <circle cx="16" cy="16" r="10.5" fill="#115E59" />
        <path
          d="M16 5.2 17.4 10.4 16 9.7 14.6 10.4ZM26.8 16 21.6 17.4 22.3 16 21.6 14.6ZM16 26.8 14.6 21.6 16 22.3 17.4 21.6ZM5.2 16 10.4 14.6 9.7 16 10.4 17.4Z"
          fill="#99F6E4"
        />
        <path d="M16 6.8 22.6 24.2 16 20.6 9.4 24.2Z" fill="#FFFFFF" />
        <circle cx="16" cy="16" r="2.1" fill="#0F766E" />
      </svg>
      <span className="text-lg font-semibold tracking-tight">
        <span className="text-ink">Biz</span>
        <span className="text-brand-600">Pilot</span>
      </span>
    </Link>
  );
}
