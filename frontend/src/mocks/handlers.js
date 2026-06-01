import { http, HttpResponse, delay } from 'msw';

const alerts = [
  {
    id: 'ALT-001',
    pathogen: 'Klebsiella pneumoniae',
    drugClass: 'Carbapenem',
    county: 'Nairobi',
    subCounty: 'Nairobi East',
    riskScore: 89,
    summary: '34% rise in carbapenem-resistant K. pneumoniae over 6 weeks.',
    triggeredAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    anomalyType: 'spike',
    status: 'active',
    sector: 'human',
  },
  {
    id: 'ALT-002',
    pathogen: 'Escherichia coli',
    drugClass: 'ESBL',
    county: 'Mombasa',
    subCounty: 'Mombasa Central',
    riskScore: 95,
    summary: 'ESBL E. coli exceeding critical threshold in multiple facilities.',
    triggeredAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    anomalyType: 'threshold_breach',
    status: 'active',
    sector: 'human',
  },
  {
    id: 'ALT-003',
    pathogen: 'Escherichia coli',
    drugClass: 'Fluoroquinolone',
    county: 'Kiambu',
    subCounty: 'Ruiru',
    riskScore: 78,
    summary: 'Fluoroquinolone resistance rising in poultry isolates.',
    triggeredAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    anomalyType: 'trend',
    status: 'active',
    sector: 'poultry',
  },
];

export const handlers = [
  http.get('/api/summary', async ({ request }) => {
    await delay(300);
    const url = new URL(request.url);
    const role = url.searchParams.get('role') || 'national';
    return HttpResponse.json({
      totalIsolates: role === 'national' ? 527 : 84,
      activeAnomalies: role === 'national' ? 7 : 2,
      countiesReporting: 12,
      oneHealthSignals: 3,
    });
  }),

  http.get('/api/map/choropleth', async () => {
    await delay(500);
    return HttpResponse.json({
      type: 'FeatureCollection',
      features: [
        { type: 'Feature', properties: { county: 'Nairobi', resistanceRate: 0.34, riskLevel: 'high' }, geometry: { type: 'Point', coordinates: [36.8219, -1.2921] } },
        { type: 'Feature', properties: { county: 'Mombasa', resistanceRate: 0.28, riskLevel: 'high' }, geometry: { type: 'Point', coordinates: [39.6682, -4.0435] } },
        { type: 'Feature', properties: { county: 'Kiambu', resistanceRate: 0.22, riskLevel: 'medium' }, geometry: { type: 'Point', coordinates: [36.8356, -1.1718] } },
        { type: 'Feature', properties: { county: 'Nakuru', resistanceRate: 0.18, riskLevel: 'medium' }, geometry: { type: 'Point', coordinates: [36.0666, -0.3031] } },
        { type: 'Feature', properties: { county: 'Kisumu', resistanceRate: 0.15, riskLevel: 'low' }, geometry: { type: 'Point', coordinates: [34.761, -0.1022] } },
      ],
    });
  }),

  http.get('/api/alerts', async ({ request }) => {
    await delay(200);
    const url = new URL(request.url);
    const role = url.searchParams.get('role') || 'national';
    const filtered = role === 'county' ? alerts.filter(a => a.county === 'Kiambu') : alerts;
    return HttpResponse.json(filtered);
  }),

  http.get('/api/alerts/:alertId', async ({ params }) => {
    await delay(200);
    const alert = alerts.find(a => a.id === params.alertId);
    if (!alert) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(alert);
  }),

  http.get('/api/alerts/:alertId/explanation', async ({ params }) => {
    await delay(400);
    const explanations = {
      'ALT-001': {
        plainTextSummary: 'This alert was triggered by a 34% rise in carbapenem-resistant K. pneumoniae in Nairobi East facilities over 6 weeks, with concurrent high carbapenem prescription volumes.',
        contributors: [
          { factor: 'Carbapenem usage volume', contributionPercent: 34 },
          { factor: 'Presence of blaNDM-1 gene', contributionPercent: 22 },
          { factor: 'Facility bed occupancy', contributionPercent: 18 },
          { factor: 'Previous month resistance baseline', contributionPercent: 26 },
        ],
      },
      'ALT-003': {
        plainTextSummary: 'Elevated fluoroquinolone resistance in poultry E. coli isolates in Ruiru sub-county linked to high antibiotic usage in feed.',
        contributors: [
          { factor: 'Antibiotic use in poultry feed', contributionPercent: 45 },
          { factor: 'Import of day-old chicks', contributionPercent: 30 },
          { factor: 'Local temperature anomaly', contributionPercent: 15 },
          { factor: 'Water source contamination', contributionPercent: 10 },
        ],
      },
    };
    const data = explanations[params.alertId] || {
      plainTextSummary: 'Detailed explanation being generated.',
      contributors: [],
    };
    return HttpResponse.json(data);
  }),

  http.get('/api/alerts/:alertId/guidance', async ({ request, params }) => {
    await delay(500);
    const url = new URL(request.url);
    const role = url.searchParams.get('role') || 'national';
    const guidance = {
      'ALT-001': {
        national: {
          summaryText: 'Policy trigger: Carbapenem resistance hotspot detected. Recommend targeted stewardship intervention.',
          recommendations: [
            'Deploy rapid response team to Nairobi East facilities.',
            'Enforce carbapenem prescribing restrictions per national guidelines.',
            'Increase lab testing capacity for carbapenemase detection.',
          ],
          actionChecklist: [
            'Notify County AMR Focal Person within 24 hours.',
            'Issue advisory to all Nairobi hospitals.',
            'Prepare resource reallocation budget.',
          ],
          references: [{ title: 'Kenya National AMR Action Plan (2023-2027)', url: '#' }],
        },
      },
      'ALT-003': {
        county_vet: {
          summaryText: 'High fluoroquinolone resistance in poultry in your sub-county. Adjust empiric treatment and investigate antibiotic use in feed.',
          recommendations: [
            'Avoid fluoroquinolones as first-line treatment in poultry.',
            'Use alternative antibiotics as per Kenya VMD approved list.',
            'Conduct farm-level antibiotic usage audit.',
          ],
          actionChecklist: [
            'Review prescribing records for last 3 months.',
            'Report findings to sub-county veterinary officer.',
            'Schedule farmer education session on antimicrobial stewardship.',
          ],
          references: [{ title: 'Kenya VMD SOP 4.2: Poultry Antimicrobial Use', url: '#' }],
        },
      },
    };
    const data = guidance[params.alertId]?.[role] || {
      summaryText: 'Guidance not available for this role.',
      recommendations: [],
      actionChecklist: [],
      references: [],
    };
    return HttpResponse.json(data);
  }),

  http.get('/api/trends', async ({ request }) => {
    await delay(300);
    const url = new URL(request.url);
    const pathogen = url.searchParams.get('pathogen') || 'Klebsiella pneumoniae';
    const drug = url.searchParams.get('drug') || 'Carbapenem';
    const months = parseInt(url.searchParams.get('months') || '12', 10);
    const series = [];
    const baseRate = pathogen === 'Klebsiella pneumoniae' ? 0.15 : 0.18;
    for (let i = months - 1; i >= 0; i--) {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      let resistanceRate = baseRate + Math.random() * 0.05;
      if (pathogen === 'Klebsiella pneumoniae' && i <= 2 && drug === 'Carbapenem') {
        resistanceRate = 0.3 + Math.random() * 0.08;
      }
      series.push({
        date: date.toISOString().split('T')[0],
        resistanceRate: parseFloat(resistanceRate.toFixed(3)),
        anomalyFlag: pathogen === 'Klebsiella pneumoniae' && i <= 1 && drug === 'Carbapenem',
      });
    }
    return HttpResponse.json({ series });
  }),

  // Catch‑all for any unhandled API request – returns 404 instead of bypassing to network
  http.all('/api/*', async () => {
    await delay(50);
    return new HttpResponse(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
  }),
];