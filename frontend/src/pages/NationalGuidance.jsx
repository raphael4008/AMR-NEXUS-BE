import { FileText, ExternalLink, Download, Share2 } from 'lucide-react';
import { DataCard } from '../components/ui/DataCard';

const items = [
  { title: 'Carbapenem Stewardship Protocol', category: 'Policy', desc: 'National guidelines for carbapenem prescribing restrictions during outbreak events.' },
  { title: 'ESBL Surveillance Guidelines', category: 'Clinical', desc: 'Updated empiric treatment recommendations for ESBL-producing Enterobacteriaceae.' },
  { title: 'One Health Coordination Framework', category: 'Policy', desc: 'Cross-sector coordination protocols for AMR signal response.' },
];

export default function NationalGuidance() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-[var(--text-primary)] tracking-tight">Guidance Hub</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-0.5">Stewardship recommendations and policy documents</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, idx) => (
          <DataCard key={idx}>
            <span className="pill pill-cyan text-[10px] mb-2 inline-block">{item.category}</span>
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