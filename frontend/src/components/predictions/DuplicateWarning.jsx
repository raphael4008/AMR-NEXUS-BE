export default function DuplicateWarning({ duplicate }) {
  if (!duplicate) return null;
  return (
    <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-xl">
      <p className="text-sm text-yellow-800">⚠️ Possible duplicate: A similar record (same pathogen, county, antibiotic class, month) was submitted recently.</p>
    </div>
  );
}