// What's here: the datasets covering a field (CDS MOC server), grouped for the tab and
// summarized for the agent. Pure functions over Field.datasets.
import type { Dataset } from './types';

// image: an image survey the map can show; drawable: a catalogue the map can draw (catalogue
// HiPS); table: a catalogue without one (a VizieR table the data agent can add); cube: a data cube.
export type Kind = 'image' | 'drawable' | 'table' | 'cube';
export const KINDS: Kind[] = ['image', 'drawable', 'table', 'cube'];
export const KIND_LABELS: Record<Kind, string> = { image: 'Images', drawable: 'Catalogues on the map', table: 'Tables', cube: 'Cubes' };
// Wavelength order, long to short; anything else last.
export const REGIMES = ['Radio', 'Millimeter', 'Infrared', 'Optical', 'UV', 'X-ray', 'Gamma-ray', 'Unspecified'];

export function kindOf(d: Dataset): Kind | null {
  if (d.type === 'image') return 'image';
  if (d.type === 'catalog') return d.url ? 'drawable' : 'table';
  return d.type === 'cube' ? 'cube' : null;
}

/** A survey's family: its id's first three parts (CDS/P/2MASS for 2MASS's J, H, K and colour). */
export const familyOf = (id: string) => id.split('/').slice(0, 3).join('/');

const regimeRank = (regime: string) => {
  const i = REGIMES.indexOf(regime);
  return i < 0 ? REGIMES.length : i;
};

export interface RegimeGroup { regime: string; datasets: Dataset[]; counts: Record<Kind, number> }

/** Datasets matching a search and kinds, by regime (long wavelengths first), widest first within. */
export function groupDatasets(datasets: Dataset[], query = '', kinds: Kind[] = KINDS): RegimeGroup[] {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  const groups = new Map<string, RegimeGroup>();
  for (const d of datasets) {
    const kind = kindOf(d);
    if (!kind || !kinds.includes(kind)) continue;
    const text = `${d.title} ${d.id} ${d.regime}`.toLowerCase();
    if (!words.every((word) => text.includes(word))) continue;
    let group = groups.get(d.regime);
    if (!group) groups.set(d.regime, group = { regime: d.regime, datasets: [], counts: { image: 0, drawable: 0, table: 0, cube: 0 } });
    group.datasets.push(d);
    group.counts[kind]++;
  }
  return [...groups.values()].sort((a, b) => regimeRank(a.regime) - regimeRank(b.regime));
}

/** What the agent is told: counts per regime and kind, and the widest few it can show. */
export function datasetsSummary(datasets: Dataset[], perRegime = 3) {
  const byRegime: Record<string, Record<Kind, number> & { widest: { id: string; title: string; kind: Kind }[] }> = {};
  for (const group of groupDatasets(datasets)) {
    const families = new Set<string>();
    const widest = [];
    for (const d of group.datasets) {
      const kind = kindOf(d)!;
      if ((kind === 'image' || kind === 'drawable') && !families.has(familyOf(d.id)) && widest.length < perRegime) {
        families.add(familyOf(d.id));
        widest.push({ id: d.id, title: d.title, kind });
      }
    }
    byRegime[group.regime] = { ...group.counts, widest };
  }
  return { total: datasets.length, byRegime };
}

const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 });  // 910M, 1.8B

/** One line about a dataset's depth: rows for catalogues, pixel size for images. */
export function datasetDetail(d: Dataset): string {
  if (d.rows !== null) return `${compact.format(d.rows)} rows`;
  if (d.pixel_arcsec !== null) {
    const p = d.pixel_arcsec;
    return p >= 60 ? `${+(p / 60).toPrecision(2)}′ pixels` : `${+p.toPrecision(2)}″ pixels`;
  }
  return '';
}
