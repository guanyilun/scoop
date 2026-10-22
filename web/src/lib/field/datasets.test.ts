import { describe, expect, it } from 'vitest';
import { datasetDetail, datasetsSummary, groupDatasets, kindOf } from './datasets';
import type { Dataset } from './types';

const d = (id: string, regime: string, type: string, extra: Partial<Dataset> = {}): Dataset =>
  ({ id, title: id.split('/').at(-1)!, regime, type, sky_fraction: null, rows: null, url: null, pixel_arcsec: null, ...extra });
const ALL = [
  d('CDS/P/2MASS/J', 'Infrared', 'image'), d('CDS/P/2MASS/H', 'Infrared', 'image'), d('CDS/P/WISE/W1', 'Infrared', 'image'),
  d('CDS/P/DSS2/red', 'Optical', 'image'), d('CDS/I/355/gaiadr3', 'Optical', 'catalog', { url: 'https://x', rows: 1.8e9 }),
  d('CDS/J/ApJ/1/1/t1', 'Optical', 'catalog'), d('CDS/P/LABHI/RGB', 'Radio', 'image', { pixel_arcsec: 51.5 }),
  d('ivoa/obscore', 'Unspecified', 'unknown')];

describe("What's here", () => {
  it('sorts datasets into kinds: images, drawable catalogues, tables, cubes', () => {
    expect(ALL.map(kindOf)).toEqual(['image', 'image', 'image', 'image', 'drawable', 'table', 'image', null]);
  });

  it('groups by regime, long wavelengths first, and filters by words and kinds', () => {
    expect(groupDatasets(ALL).map((g) => g.regime)).toEqual(['Radio', 'Infrared', 'Optical']);
    expect(groupDatasets(ALL, '2mass').flatMap((g) => g.datasets.map((x) => x.id))).toEqual(['CDS/P/2MASS/J', 'CDS/P/2MASS/H']);
    expect(groupDatasets(ALL, 'optical', ['table']).flatMap((g) => g.datasets.map((x) => x.id))).toEqual(['CDS/J/ApJ/1/1/t1']);
    expect(groupDatasets(ALL).find((g) => g.regime === 'Optical')!.counts).toEqual({ image: 1, drawable: 1, table: 1, cube: 0 });
  });

  it('tells the agent one survey per family, never a table', () => {
    const summary = datasetsSummary(ALL);
    expect(summary.total).toBe(8);
    expect(summary.byRegime.Infrared.widest.map((w) => w.id)).toEqual(['CDS/P/2MASS/J', 'CDS/P/WISE/W1']);
    expect(summary.byRegime.Optical.widest.map((w) => w.kind)).toEqual(['image', 'drawable']);
  });

  it('describes depth in rows or pixel size', () => {
    expect(datasetDetail(ALL[4])).toBe('1.8B rows');
    expect(datasetDetail(ALL[6])).toBe('52″ pixels');
    expect(datasetDetail(d('x/y', 'Radio', 'image', { pixel_arcsec: 206 }))).toBe('3.4′ pixels');
    expect(datasetDetail(ALL[0])).toBe('');
  });
});
