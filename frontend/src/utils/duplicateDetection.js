export function isDuplicate(newRecord, recentPredictions) {
  // Simple heuristic: same pathogen, county, antibiotic class, and sample month
  return recentPredictions.some(p =>
    p.pathogen_code === newRecord.pathogen_code &&
    p.county === newRecord.county &&
    p.antibiotic_class === newRecord.antibiotic_class &&
    p.sample_month === newRecord.sample_month
  );
}
