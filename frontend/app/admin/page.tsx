"use client";

import { FormEvent, useEffect, useState } from "react";
import { Activity, DatabaseZap, RefreshCw, Sparkles } from "lucide-react";

import { Badge, Metric, PageHeader, Surface } from "@/components/ui";
import { createAdminUpdate, createScrapingJob, fetchOperationalStatus } from "@/lib/api.mjs";

type AdminUpdate = {
  dataset: string;
  rows_inserted?: number;
  rows_rejected?: number;
  rows_updated?: number;
  source_url?: string;
  status: string;
  summary?: string;
};

type ScrapingJob = {
  dataset: string;
  job_type?: string;
  row_count?: number;
  source_url?: string;
  status: string;
};

export default function AdminPage() {
  const [updates, setUpdates] = useState<AdminUpdate[]>([]);
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [aiConfigured, setAiConfigured] = useState(false);
  const [status, setStatus] = useState("Loading operations state.");
  const [dataset, setDataset] = useState("cutoff_data");
  const [sourceUrl, setSourceUrl] = useState("");

  useEffect(() => {
    fetchOperationalStatus()
      .then((payload) => {
        setUpdates(payload.adminUpdates);
        setJobs(payload.scrapingJobs);
        setAiConfigured(Boolean(payload.ai.configured));
        setStatus("Manual updates, scraping jobs, and AI configuration loaded.");
      })
      .catch(() => {
        setUpdates([{ dataset: "cutoff_data", status: "needs_review", summary: "Manual update console is in preview mode." }]);
        setJobs([{ dataset: "seat_matrix", job_type: "real_time_scraping", row_count: 0, status: "ready" }]);
        setStatus("Operations API unavailable. Preview status remains visible.");
      });
  }, []);

  const submitManualUpdate = async (event: FormEvent) => {
    event.preventDefault();
    const payload = {
      dataset,
      source_url: sourceUrl || undefined,
      rows_inserted: 0,
      rows_updated: 0,
      rows_rejected: 0,
    };
    try {
      const update = await createAdminUpdate(payload);
      setUpdates((current) => [update, ...current].slice(0, 8));
      setStatus(`${dataset} manual update recorded for review.`);
    } catch {
      setStatus("Manual update could not reach the API.");
    }
  };

  const queueScrape = async () => {
    try {
      const job = await createScrapingJob({
        dataset,
        source_url: sourceUrl || undefined,
        status: "queued",
        row_count: 0,
      });
      setJobs((current) => [job, ...current].slice(0, 8));
      setStatus(`${dataset} scraping job queued.`);
    } catch {
      setStatus("Scraping job could not reach the API.");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        description="Full admin automation for manual updates, source freshness, real-time scraping status, and AI availability."
        eyebrow="Admin automation"
        title="Keep source data auditable."
      />

      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{status}</p>

      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="AI guidance" note="Provider configuration" value={aiConfigured ? "Configured" : "Fallback"} />
        <Metric label="Admin updates" note="Recent manual records" value={`${updates.length}`} />
        <Metric label="Scraping jobs" note="Automation queue" value={`${jobs.length}`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Surface className="space-y-4 p-5" tone="paper">
          <div className="flex items-center gap-2">
            <DatabaseZap className="h-5 w-5 text-counsly-coral" />
            <h2 className="font-display text-3xl text-counsly-ink">Source action</h2>
          </div>
          <form className="space-y-3" onSubmit={submitManualUpdate}>
            <label className="field-label">
              Dataset
              <select className="field" onChange={(event) => setDataset(event.target.value)} value={dataset}>
                <option value="cutoff_data">Cutoff data</option>
                <option value="seat_matrix">Seat matrix</option>
                <option value="rank_list">Rank list</option>
                <option value="college_master">College master</option>
              </select>
            </label>
            <label className="field-label">
              Official source URL
              <input className="field" onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://..." value={sourceUrl} />
            </label>
            <div className="flex flex-wrap gap-2">
              <button className="button-primary" type="submit">Record manual update</button>
              <button className="button-secondary" onClick={queueScrape} type="button">
                <RefreshCw className="h-4 w-4" /> Queue scrape
              </button>
            </div>
          </form>
        </Surface>

        <div className="grid gap-4 xl:grid-cols-2">
          <Surface className="space-y-4 p-5" tone="soft">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-counsly-coral" />
              <h2 className="font-display text-3xl text-counsly-ink">Manual updates</h2>
            </div>
            {updates.map((item, index) => (
              <article className="rounded-lg border border-counsly-line bg-counsly-canvas p-4" key={`${item.dataset}-${index}`}>
                <div className="mb-2 flex items-center gap-2">
                  <Badge tone={item.status === "applied" ? "safe" : "warning"}>{item.status}</Badge>
                  <span className="font-mono text-xs text-counsly-muted">{item.dataset}</span>
                </div>
                <p className="text-sm leading-6 text-counsly-body">{item.summary || "Manual update ready for operator review."}</p>
              </article>
            ))}
          </Surface>

          <Surface className="space-y-4 p-5" tone="dark">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-counsly-coral" />
              <h2 className="font-display text-3xl text-white">Scraping automation</h2>
            </div>
            {jobs.map((job, index) => (
              <article className="rounded-lg bg-counsly-slate p-4" key={`${job.dataset}-${index}`}>
                <div className="mb-2 flex items-center gap-2">
                  <Badge tone="dark">{job.status}</Badge>
                  <span className="font-mono text-xs text-counsly-card">{job.job_type || "real_time_scraping"}</span>
                </div>
                <h3 className="font-medium text-white">{job.dataset}</h3>
                <p className="mt-1 text-sm text-counsly-card">{job.row_count || 0} rows observed from {job.source_url || "configured official source"}.</p>
              </article>
            ))}
          </Surface>
        </div>
      </div>
    </div>
  );
}
