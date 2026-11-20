import { LandingView } from "@/components/landing/LandingView";
import { fetchHealthReady } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const health = await fetchHealthReady();
  return <LandingView apiOk={health.ok} />;
}
