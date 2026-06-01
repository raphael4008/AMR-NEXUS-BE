import { FileText, ExternalLink, Download, Share2 } from 'lucide-react';
import { DataCard } from '../components/ui/DataCard';

const items = [
  { title: 'Poultry Antimicrobial Stewardship', category: 'Clinical', desc: 'Kenya VMD SOP 4.2 — Guidelines for prudent antimicrobial use in poultry production.' },
  { title: 'Fluoroquinolone Alternatives', category: 'Prescribing', desc: 'Recommended alternative antibiotics when fluoroquinolone resistance exceeds 20% threshold.' },
  { title: 'Farm Biosecurity Protocol', category: 'Prevention', desc: 'Standard operating procedures for preventing AMR spread in poultry farms.' },
];

export default function CountyGuidance() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">Stewardship Guidance</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-0.5">County-specific recommendations for antimicrobial stewardship</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, idx) => (
          <DataCard key={idx}>
            <span className="pill pill-amber text-[10px] mb-2 inline-block">{item.category}</span>
            <h3 className="text-base font-semibold text-[var(--text-primary)] mt-2">{item.title}</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-1.5">{item.desc}</p>
            <div className="flex flex-wrap gap-2 mt-4">
              <button className="btn-primary text-xs">View Guidance</button>
              <button className="btn-secondary text-xs flex items-center gap-1"><Download className="w-3 h-3" /> Download</button>
              <button className="btn-secondary text-xs flex items-center gap-1"><Share2 className="w-3 h-3" /> Share</button>
            </div>
          </DataCard>
        ))}
      </div>
    </div>
  );
}