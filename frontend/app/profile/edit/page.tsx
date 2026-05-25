"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { useApp } from "@/app/AppContext";
import { Badge, PageHeader, Surface } from "@/components/ui";
import { fetchWorkspaceSettings, updateWorkspaceSettings } from "@/lib/api.mjs";
import { branches, districts } from "@/lib/product";

export default function ProfileEditPage() {
  const { user } = useApp();
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState("Loading workspace defaults.");
  const [settings, setSettings] = useState({
    compactView: false,
    defaultDistrict: "Chennai",
    mobileDensity: "default",
    preferredBranches: branches.slice(0, 3).map((branch) => branch.code),
    themeMode: "mild",
  });

  useEffect(() => {
    fetchWorkspaceSettings()
      .then((next) => {
        setSettings((current) => ({
          ...current,
          ...next,
          defaultDistrict: next.defaultDistrict || current.defaultDistrict,
          preferredBranches: next.preferredBranches.length ? next.preferredBranches : current.preferredBranches,
        }));
        setStatus("Workspace defaults loaded from the API.");
      })
      .catch(() => setStatus("API defaults unavailable. Changes remain useful in preview mode."));
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const persisted = await updateWorkspaceSettings(settings);
      setSettings((current) => ({ ...current, ...persisted }));
      setStatus("Workspace defaults saved.");
    } catch {
      setStatus("Defaults saved in the current form only because the workspace API did not respond.");
    }
    setSaved(true);
  };

  const toggleBranch = (code: string) => {
    setSettings((current) => ({
      ...current,
      preferredBranches: current.preferredBranches.includes(code)
        ? current.preferredBranches.filter((branch) => branch !== code)
        : [...current.preferredBranches, code],
    }));
  };

  return (
    <div className="space-y-6">
      <PageHeader description="Defaults for district fit, branch filters, compact density, and saved guidance state." eyebrow="Profile" title="Tune the workspace to the student." />
      <p className="rounded-xl border border-counsly-line bg-counsly-canvas px-4 py-3 text-sm text-counsly-body">{status}</p>
      <form className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]" onSubmit={submit}>
        <Surface className="space-y-4 p-6" tone="paper">
          <Badge>{user?.google_email ?? "Local preview profile"}</Badge>
          <label className="field-label">
            Home district
            <select className="field" onChange={(event) => setSettings((current) => ({ ...current, defaultDistrict: event.target.value }))} value={settings.defaultDistrict}>
              {districts.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <fieldset className="space-y-2">
            <legend className="field-label">Preferred branches</legend>
            <div className="grid gap-2 md:grid-cols-2">
              {branches.map((branch) => (
                <label className="flex min-h-11 items-center gap-3 rounded-lg border border-counsly-line p-3 text-sm text-counsly-body" key={branch.code}>
                  <input checked={settings.preferredBranches.includes(branch.code)} onChange={() => toggleBranch(branch.code)} type="checkbox" />
                  {branch.name}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="grid gap-2 md:grid-cols-2">
            <label className="flex min-h-11 items-center gap-3 rounded-lg border border-counsly-line p-3 text-sm text-counsly-body">
              <input checked={settings.compactView} onChange={(event) => setSettings((current) => ({ ...current, compactView: event.target.checked }))} type="checkbox" />
              Use compact choice density
            </label>
            <label className="field-label">
              Mobile density
              <select className="field" onChange={(event) => setSettings((current) => ({ ...current, mobileDensity: event.target.value }))} value={settings.mobileDensity}>
                <option value="default">Default</option>
                <option value="compact">Compact</option>
                <option value="comfortable">Comfortable</option>
              </select>
            </label>
          </div>
          <button className="button-primary w-fit" type="submit">Save profile defaults</button>
        </Surface>

        <Surface className="space-y-4 p-6" tone="soft">
          <h2 className="font-display text-3xl text-counsly-ink">Workspace boundary</h2>
          <p className="text-sm leading-6 text-counsly-body">Choices, compares, snapshots, and settings stay private to this student profile.</p>
          {saved && (
            <p className="flex items-center gap-2 rounded-lg bg-counsly-safe/15 p-3 text-sm text-counsly-ink">
              <CheckCircle2 className="h-4 w-4 text-counsly-safe" />
              Defaults saved for {settings.defaultDistrict}.
            </p>
          )}
        </Surface>
      </form>
    </div>
  );
}
