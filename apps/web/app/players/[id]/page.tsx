import { api } from "@/lib/api";
import { PlayerCard } from "@/components/PlayerCard";

export default async function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const player = await api.player(Number(id));
  return <PlayerCard player={player} />;
}

