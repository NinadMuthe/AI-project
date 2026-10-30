// frontend/src/components/SummaryCard.tsx
import React from "react";

interface SummaryCardProps {
  title: string;
  value: string | number;
  color?: string; // Tailwind text color class, e.g., "text-primary"
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, color = "text-primary" }) => {
  return (
    <div className="bg-white rounded shadow p-4 flex flex-col">
      <span className="text-sm text-muted mb-1">{title}</span>
      <span className={`text-2xl font-semibold ${color}`}>{value}</span>
    </div>
  );
};

export default SummaryCard;

