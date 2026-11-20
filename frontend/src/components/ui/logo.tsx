import { cn } from "@/lib/cn";

/** Official lockup served from /logo/BizPilot_logo.png (source: src/public/logo). */
export const LOGO_SRC = "/logo/BizPilot_logo.png";

const FULL = { w: 1536, h: 1024 };
const LOCKUP = { x: 227, y: 344, w: 1018, h: 253 };
const MARK = { x: 227, y: 344, w: 258, h: 253 };

function LogoCrop({
  region,
  height,
  width,
  alt,
  className,
  priority,
}: {
  region: { x: number; y: number; w: number; h: number };
  height: number;
  width?: number;
  alt: string;
  className?: string;
  priority?: boolean;
}) {
  const scale = height / region.h;
  const frameWidth = width ?? region.w * scale;
  return (
    <span
      className={cn("relative inline-block overflow-hidden align-middle", className)}
      style={{ width: frameWidth, height }}
      aria-hidden={alt === "" ? true : undefined}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={LOGO_SRC}
        alt={alt}
        width={FULL.w}
        height={FULL.h}
        decoding="async"
        fetchPriority={priority ? "high" : "auto"}
        className="absolute max-w-none"
        style={{
          width: FULL.w * scale,
          height: FULL.h * scale,
          left: -region.x * scale,
          top: -region.y * scale,
        }}
      />
    </span>
  );
}

export function LogoMark({ className, size = 32 }: { className?: string; size?: number }) {
  return (
    <LogoCrop
      region={MARK}
      height={size}
      width={size}
      alt=""
      className={className}
    />
  );
}

export function Logo({
  className,
  height = 32,
  priority = false,
}: {
  className?: string;
  height?: number;
  priority?: boolean;
}) {
  return (
    <LogoCrop
      region={LOCKUP}
      height={height}
      alt="BizPilot"
      className={className}
      priority={priority}
    />
  );
}
