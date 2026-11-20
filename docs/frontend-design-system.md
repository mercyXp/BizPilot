# BizPilot frontend design system

Light theme only. Teal is the brand. Other colour is semantic.

## Brand (do not change)

| Token | Hex |
| --- | --- |
| Primary text | `#0F172A` |
| Brand | `#0D9488` |
| Deep teal | `#0F766E` |
| Soft teal | `#CCFBF1` |
| Background | `#F1F5F9` |
| Surface | `#FFFFFF` |
| Border | `#E5E7EB` |
| Secondary text | `#334155` |

Typography: Inter (`--font-sans`). Geist may replace it later without changing colour.

Logo: `frontend/src/public/logo/BizPilot_logo.png` (copied to `frontend/public/logo/` for Next). Compass + wordmark lockup. Use `Logo` for the full lockup and `LogoMark` for the compass crop. Do not redraw a letter-B mark.

Source of truth: CSS variables in `frontend/src/app/globals.css`, mapped in `frontend/tailwind.config.ts`, mirrored as constants in `frontend/src/lib/colors.ts`.

## Semantic colour

Use these for meaning, never as a second brand.

- Success `#16A34A` / bg `#DCFCE7`
- Danger `#DC2626` / bg `#FEE2E2`
- Warning `#D97706` / bg `#FEF3C7`
- Information `#2563EB` / bg `#DBEAFE`
- AI `#7C3AED` / bg `#EDE9FE`
- Customer engagement `#DB2777` / bg `#FCE7F3`

Components: `Badge`, `StatusBadge`, `Alert`.

## Chart palette

Import `chartColors` from `@/lib/colors` or `chartTheme` from `@/components/charts/theme`. Do not pick ad-hoc series colours.

- Revenue `#0D9488`
- Expenses `#F59E0B`
- Profit `#16A34A`
- Purchases `#3B82F6`
- Customers `#8B5CF6`
- Sales `#EC4899`
- Outstanding `#EF4444`

Charts must include a legend or labelled tooltip. Gridlines stay `#E5E7EB`.

## Statuses

| Status | Tone |
| --- | --- |
| Paid / completed | Success |
| Pending / awaiting approval | Warning |
| Failed / rejected | Danger |
| Processing | Information |
| Draft | Muted grey |
| Cancelled | Danger (or muted when the action is archival) |
| AI-generated | AI purple |

## Motion

Tokens live in `frontend/src/lib/motion.ts` and CSS `--motion-*` variables.

| Token | Duration |
| --- | --- |
| Fast | 150ms |
| Standard | 200ms |
| Card | 250ms |
| Dropdown | 200ms |
| Sidebar | 280ms |
| Modal | 220ms |
| Section | 550ms |
| Hero | 700ms |
| Chart | 800ms |

Easing: `cubic-bezier(0.22, 1, 0.36, 1)`.

Use **CSS** for buttons, cards, inputs, links. Use **Framer Motion** for page/section entrance, staggered lists, modal/drawer, dropdown. Use **Intersection Observer** (via `whileInView` or the KPI count-up) for scroll reveals. Use the chart library’s own entrance animation (`chartTheme.animationDuration`).

`MotionConfig reducedMotion="user"` is set in `Providers`. `withReducedMotion()` swaps variants to opacity-only. CSS also short-circuits transitions when `prefers-reduced-motion: reduce`.

## Usage

```tsx
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Reveal } from "@/components/motion/Reveal";
import { chartColors } from "@/lib/colors";
```

Do not introduce dark mode. Do not use navy or charcoal as default text.
