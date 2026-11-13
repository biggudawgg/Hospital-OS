// BedTile — one bed in the ward grid: bed number, free/occupied, and the patient's initials.
import { BedDouble } from "lucide-react";
import { initials } from "../api";

export default function BedTile({ bed, patient }) {
  const occupied = bed.is_occupied;
  return (
    <div
      className={`flex flex-col gap-2 rounded-control border p-3 ${
        occupied ? "border-primary/30 bg-primary-soft" : "border-dashed border-line bg-surface"
      }`}
      title={occupied && patient ? `${bed.bed_number}: ${patient.full_name}` : `${bed.bed_number}: free`}
    >
      <div className="flex items-center justify-between">
        <span className="num text-xs font-semibold text-ink">{bed.bed_number}</span>
        <BedDouble size={14} className={occupied ? "text-primary" : "text-ink-subtle"} aria-hidden="true" />
      </div>
      {occupied ? (
        <div className="flex items-center gap-2">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-primary text-[11px] font-bold text-white">
            {initials(patient?.full_name) || "?"}
          </span>
          <span className="truncate text-xs text-ink-muted">{patient?.full_name || `Patient #${bed.patient_id}`}</span>
        </div>
      ) : (
        <span className="text-xs font-medium text-ok">Free</span>
      )}
    </div>
  );
}
