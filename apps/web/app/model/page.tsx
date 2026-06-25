import { BarChart3, BrainCircuit, CheckCircle2, FlaskConical, History, Sparkles } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { featureLabel, metricLabel } from "@/lib/labels";

type LabModel = {
  id: string;
  name: string;
  version: string;
  status: "available" | "planned";
  description: string;
  features: string[];
  weights?: Record<string, number>;
  accuracy: number | null;
  log_loss: number | null;
  brier_score: number | null;
  training_status?: string;
  training_data?: string;
  training_notes?: string[];
  limitations: string[];
};

function formatMetric(value: unknown): string {
  return typeof value === "number" ? value.toFixed(2) : "Ikke beregnet";
}

export default async function ModelPage({ searchParams }: { searchParams?: Promise<{ modell?: string }> }) {
  const params = searchParams ? await searchParams : {};
  const lab = await api.modelLab();
  const models = (Array.isArray(lab.models) ? lab.models : []) as LabModel[];
  const selectedId = params.modell ?? String(lab.active_model_id ?? models[0]?.id ?? "country");
  const selectedModel = models.find((model) => model.id === selectedId) ?? models[0];
  const versions = Array.isArray(lab.version_history) ? lab.version_history : [];
  const trainingPlan = Array.isArray(lab.training_plan) ? lab.training_plan : [];
  const selectedWeights = selectedModel?.weights ?? {};
  const featureImportance = Object.keys(selectedWeights).length
    ? Object.entries(selectedWeights)
        .map(([feature, importance]) => ({ feature, importance }))
        .sort((first, second) => second.importance - first.importance)
    : (Array.isArray(lab.feature_importance) ? lab.feature_importance : []);
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
              Velg hvilken prediksjonsmodell du vil inspisere. Modellene er deterministiske og valgbare nå, mens ekte historisk trening kobles på når verifiserte VM-data er importert.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-4">
        {models.map((model) => {
          const isSelected = selectedModel?.id === model.id;
          const isAvailable = model.status === "available";
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
                <span className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${isAvailable ? "bg-pine/10 text-pine" : "bg-ink/10 text-ink/50"}`}>
                  {isAvailable ? <CheckCircle2 size={14} /> : <FlaskConical size={14} />}
                  {isAvailable ? "Velgbar" : "Planlagt"}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/60">{model.description}</p>
              <p className="mt-3 text-xs font-bold uppercase tracking-[0.12em] text-ink/45">{model.features.length} parametre</p>
            </Link>
          );
        })}
      </section>

      {selectedModel ? (
        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="space-y-5">
            <section className="grid gap-4 md:grid-cols-3">
              {["accuracy", "log_loss", "brier_score"].map((key) => (
                <div key={key} className="metric-tile">
                  <span className="text-sm text-ink/60">{metricLabel(key)}</span>
                  <strong className="block text-3xl">{formatMetric(metrics[key as keyof typeof metrics])}</strong>
                  <p className="mt-1 text-xs text-ink/50">{selectedModel.training_status ?? "Må trenes og backtestes"}</p>
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
                    <div className="h-2 rounded-sm bg-ink/10">
                      <div className="h-2 rounded-sm bg-fjord" style={{ width: `${Math.min(item.importance * 100 * 3, 100)}%` }} />
                    </div>
                    <strong className="text-right">{Number(item.importance).toFixed(3)}</strong>
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
              {selectedModel.training_data ? <p className="mb-3 text-sm leading-6 text-ink/60">{selectedModel.training_data}</p> : null}
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
            {versions.map((item: any) => (
              <div key={item.version} className="rounded-md bg-frost p-3">
                <strong>{item.version}</strong>
                <p className="text-sm text-ink/65">{item.notes}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="surface p-4">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-md bg-fjord/10 text-fjord">
              <FlaskConical size={20} />
            </span>
            <div>
              <p className="eyebrow">Trening</p>
              <h2 className="text-lg font-semibold">Treningsløp for ekte modeller</h2>
            </div>
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            {trainingPlan.map((item: string, index: number) => (
              <div key={item} className="rounded-md bg-frost p-3 text-sm text-ink/70">
                <strong className="mr-2 text-fjord">{index + 1}</strong>{item}
              </div>
            ))}
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {["Kalibreringsgraf", "Forvekslingsmatrise", "SHAP-forklaring"].map((label) => (
              <div key={label} className="grid min-h-[130px] place-items-center rounded-lg border border-dashed border-ink/25 bg-white text-center text-sm font-semibold text-ink/50">
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
