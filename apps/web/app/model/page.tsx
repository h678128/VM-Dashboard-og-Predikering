import { BarChart3, BrainCircuit, CheckCircle2, History, Lock, Sparkles } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { featureLabel, metricLabel } from "@/lib/labels";

type LabModel = {
  id: string;
  name: string;
  version: string;
  status: "active" | "planned";
  description: string;
  features: string[];
  accuracy: number | null;
  log_loss: number | null;
  brier_score: number | null;
  limitations: string[];
};

function formatMetric(value: unknown): string {
  return typeof value === "number" ? value.toFixed(2) : "Kommer";
}

export default async function ModelPage({ searchParams }: { searchParams?: Promise<{ modell?: string }> }) {
  const params = searchParams ? await searchParams : {};
  const lab = await api.modelLab();
  const models = (Array.isArray(lab.models) ? lab.models : []) as LabModel[];
  const selectedId = params.modell ?? String(lab.active_model_id ?? models[0]?.id ?? "simple");
  const selectedModel = models.find((model) => model.id === selectedId) ?? models[0];
  const featureImportance = Array.isArray(lab.feature_importance) ? lab.feature_importance : [];
  const versions = Array.isArray(lab.version_history) ? lab.version_history : [];
  const metrics = selectedModel
    ? {
        accuracy: selectedModel.accuracy,
        log_loss: selectedModel.log_loss,
        brier_score: selectedModel.brier_score
      }
    : ((lab.backtesting ?? {}) as Record<string, unknown>);

  return (
    <div className="space-y-5">
      <section className="surface p-5 md:p-6">
        <div className="flex items-start gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-md bg-fjord/10 text-fjord">
            <BrainCircuit size={22} />
          </span>
          <div>
            <p className="eyebrow">Modellinnsikt</p>
            <h1 className="mt-1 text-3xl font-bold">Modellverksted</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-ink/60">
              Velg mellom en enkel aktiv modell, neste planlagte landmodell og en senere avansert modell. Tallene er seedet for portfolio-demoen, men strukturen viser hvordan modellene kan sammenlignes.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-3">
        {models.map((model) => {
          const isSelected = selectedModel?.id === model.id;
          const isActive = model.status === "active";
          return (
            <Link
              key={model.id}
              className={`focus-ring rounded-lg border p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md ${isSelected ? "border-fjord bg-white" : "border-ink/10 bg-white/75"}`}
              href={`/model?modell=${model.id}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-ink/40">{model.version}</p>
                  <h2 className="mt-1 text-lg font-bold">{model.name}</h2>
                </div>
                <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${isActive ? "bg-pine/10 text-pine" : "bg-ink/10 text-ink/50"}`}>
                  {isActive ? <CheckCircle2 size={14} /> : <Lock size={14} />}
                  {isActive ? "Aktiv" : "Kommer"}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/60">{model.description}</p>
            </Link>
          );
        })}
      </section>

      {selectedModel ? (
        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-5">
            <section className="grid gap-4 md:grid-cols-3">
              {["accuracy", "log_loss", "brier_score"].map((key) => (
                <div key={key} className="metric-tile">
                  <span className="text-sm text-ink/60">{metricLabel(key)}</span>
                  <strong className="block text-3xl">{formatMetric(metrics[key as keyof typeof metrics])}</strong>
                  <p className="mt-1 text-xs text-ink/50">{selectedModel.status === "active" ? "Seedet backtest" : "Må trenes og backtestes"}</p>
                </div>
              ))}
            </section>

            <section className="surface p-4">
              <div className="mb-4 flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-md bg-fjord/10 text-fjord">
                  <BarChart3 size={20} />
                </span>
                <div>
                  <p className="eyebrow">Forklaring</p>
                  <h2 className="text-lg font-semibold">Variabelbetydning</h2>
                </div>
              </div>
              <div className="space-y-3">
                {featureImportance.map((item: any) => (
                  <div key={item.feature} className="grid grid-cols-[150px_minmax(0,1fr)_52px] items-center gap-3 text-sm">
                    <span className="truncate">{featureLabel(item.feature)}</span>
                    <div className="h-2 rounded-sm bg-ink/10"><div className="h-2 rounded-sm bg-fjord" style={{ width: `${Math.min(item.importance * 100 * 3, 100)}%` }} /></div>
                    <strong className="text-right">{item.importance}</strong>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <aside className="space-y-5">
            <section className="surface p-4">
              <div className="mb-4 flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-md bg-pine/10 text-pine">
                  <Sparkles size={20} />
                </span>
                <div>
                  <p className="eyebrow">Valgt modell</p>
                  <h2 className="text-lg font-semibold">{selectedModel.name}</h2>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                {selectedModel.features.map((feature) => (
                  <div key={feature} className="rounded-md bg-frost px-3 py-2 font-semibold text-ink/70">
                    {featureLabel(feature)}
                  </div>
                ))}
              </div>
            </section>

            <section className="surface p-4">
              <p className="eyebrow">Begrensninger</p>
              <div className="mt-3 space-y-2 text-sm text-ink/65">
                {selectedModel.limitations.map((item) => (
                  <p key={item} className="rounded-md bg-frost p-3">{item}</p>
                ))}
              </div>
            </section>
          </aside>
        </section>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="surface p-4">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-md bg-pine/10 text-pine">
              <History size={20} />
            </span>
            <div>
              <p className="eyebrow">Historikk</p>
              <h2 className="text-lg font-semibold">Versjoner</h2>
            </div>
          </div>
          <div className="space-y-2">
            {versions.map((item: any) => <div key={item.version} className="rounded-md bg-frost p-3"><strong>{item.version}</strong><p className="text-sm text-ink/65">{item.notes}</p></div>)}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {["Kalibreringsgraf", "Forvekslingsmatrise", "SHAP-forklaring"].map((label) => (
            <div key={label} className="grid min-h-[180px] place-items-center rounded-lg border border-dashed border-ink/25 bg-white text-center text-sm font-semibold text-ink/50">
              {label}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
