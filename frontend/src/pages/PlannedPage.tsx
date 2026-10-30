// frontend/src/pages/PlannedPage.tsx
import React from "react";

interface PlannedPageProps {
  featureName: string;
  description: string;
  icon?: string;
}

const PlannedPage: React.FC<PlannedPageProps> = ({ featureName, description, icon = "🚀" }) => {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="w-16 h-16 bg-indigo-50 border border-indigo-200 rounded-2xl flex items-center justify-center text-3xl shadow-sm mb-4">
        {icon}
      </div>
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200 mb-3">
        Planned: next phase
      </span>
      <h1 className="text-2xl font-bold text-slate-800 mb-2">{featureName}</h1>
      <p className="max-w-md text-sm text-slate-500 mb-6">{description}</p>
      <div className="bg-white border border-slate-200 rounded-lg p-4 max-w-sm w-full text-left shadow-sm">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Roadmap Target</h4>
        <div className="flex items-center text-xs text-slate-600">
          <span className="w-2 h-2 rounded-full bg-indigo-500 mr-2"></span>
          Scheduled for Phase 2 Deployment
        </div>
      </div>
    </div>
  );
};

export default PlannedPage;
