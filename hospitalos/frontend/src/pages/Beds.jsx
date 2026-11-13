// Beds page — every ward with an occupancy ring and a grid of bed tiles.
import { useState } from "react";
import { useApiMany } from "../api";
import TopBar from "../components/TopBar";
import BedTile from "../components/BedTile";
import OccupancyRing from "../components/OccupancyRing";
import { SkeletonGrid } from "../components/SkeletonCard";
import { EmptyState, ErrorState } from "../components/States";

const FILTERS = [["all", "All beds"], ["free", "Free"], ["occupied", "Occupied"]];

export default function Beds() {
  const { data, loading, error, reload } = useApiMany({ beds: "/beds", wards: "/wards", patients: "/patients" });
  const [filter, setFilter] = useState("all");

  const patientById = Object.fromEntries((data?.patients || []).map((p) => [p.id, p]));
  const visible = (bed) => filter === "all" || (filter === "free" ? !bed.is_occupied : bed.is_occupied);

  return (
    <>
      <TopBar title="Beds" subtitle="Occupancy by ward"
        actions={
          <div className="flex rounded-control border border-line bg-surface p-0.5" role="tablist">
            {FILTERS.map(([key, label]) => (
              <button key={key} role="tab" aria-selected={filter === key} onClick={() => setFilter(key)}
                className={`rounded-[8px] px-3 py-1.5 text-sm font-medium ${filter === key ? "bg-primary text-white" : "text-ink-muted"}`}>
                {label}
              </button>
            ))}
          </div>
        } />
      <main className="space-y-5 p-6">
        {error && <ErrorState message={error} onRetry={reload} />}
        {loading && <SkeletonGrid count={3} className="grid gap-4" />}
        {data && data.wards.length === 0 && <EmptyState title="No wards yet" message="Run the seed script to create wards and beds." />}
        {data && data.wards.map((ward) => {
          const wardBeds = data.beds.filter((b) => b.ward_id === ward.id);
          const occupied = wardBeds.filter((b) => b.is_occupied).length;
          const shown = wardBeds.filter(visible);
          return (
            <section key={ward.id} className="card flex flex-col gap-5 p-5 md:flex-row" aria-label={`${ward.name} ward`}>
              <div className="flex shrink-0 flex-col items-center gap-1 md:w-36">
                <OccupancyRing occupied={occupied} total={wardBeds.length} size={88} />
                <h2 className="text-base font-semibold">{ward.name}</h2>
                <p className="text-xs text-ink-muted">Floor {ward.floor} · {wardBeds.length - occupied} free</p>
              </div>
              <div className="grid flex-1 grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">
                {shown.map((bed) => <BedTile key={bed.id} bed={bed} patient={patientById[bed.patient_id]} />)}
                {shown.length === 0 && <p className="col-span-full text-sm text-ink-muted">No beds match this filter.</p>}
              </div>
            </section>
          );
        })}
      </main>
    </>
  );
}
