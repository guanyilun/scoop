---
name: exoplanets_tess
description: Confirmed exoplanets and their hosts (NASA Exoplanet Archive), TESS Objects
  of Interest, TIC stars and TESS light curves, and HST/JWST exoplanet spectra and time
  series. What each table holds, what its values mean (measured vs estimated masses), the
  TESS light-curve limits, and who answers what. Load before adding or describing these
  tables, or before relaying the exoplanet agent's answer.
used_by: [chat agent, data agent, exoplanet agent (as prompt guidance)]
status: draft
sources_checked: 2026-10-22 (NASA Exoplanet Archive TAP counts and its pscomppars
  documentation; SCOOP's scoop/exoplanets code)
---

# Exoplanets and TESS

## Who does what
- **The exoplanet agent** (`ask_exoplanet_agent`) answers questions about planets, papers,
  TOIs and light curves. Every claim it makes quotes a tool result, and code checks the
  quotes before the user sees them. Relay its answer word for word, including its
  checked or not-checked line; never add numbers to it.
- **The data agent** adds the tables below to a field (`add_data`), so they can be drawn,
  filtered and highlighted.
- The exoplanet agent's paper lookups use SCOOP's one ADS client, so the papers it reads
  appear in the Literature panel.

## The tables
| Table | What | From |
|---|---|---|
| `exoplanet_hosts` | Confirmed planet hosts in the field, each with its planets | NASA Exoplanet Archive, `pscomppars` (one row per planet) |
| `tess_tois` | TESS Objects of Interest: candidates, with the TFOPWG disposition (e.g. PC, CP, FP) | NASA Exoplanet Archive, `toi` |
| `tic` | TESS Input Catalog stars: Tmag, Teff, radius, log g, contamination ratio `Rcont` | TIC v8.2, VizieR `IV/39/tic82` |
| `hst_jwst_spectra` | HST/JWST spectra, time series (transits and eclipses) and IFU cubes, executed and planned | MAST |

The field pipeline's `observations` table holds HST/JWST *images* only, so it misses most
exoplanet observations; `hst_jwst_spectra` is where transit spectroscopy shows up.

## What the values mean
- **`pscomppars` is not self-consistent.** It has one row per planet, filled in from
  several papers. The archive says the values are "often drawn from multiple references"
  and the set "may not be internally consistent". For a self-consistent solution, read
  one paper's values (the `ps` table, or the paper itself). Values the archive calculated
  itself carry the reference "Calculated Value" and no uncertainties.
- **Most masses are not measured.** On 2026-10-22, of 6,451 planets in `pscomppars`:
  - 2,477 had a measured mass;
  - 924 only a minimum mass (M sin i);
  - 15 had M sin i / sin i;
  - 3,035 (47%) a mass estimated from the radius with a mass–radius relation.

  `pl_bmassprov` says which. Never present an estimated mass as measured.
- **A TOI is a candidate.** Its disposition says how far follow-up has got: false
  positives stay in the table.
- **Archive positions are at epoch 2016**, not J2000. A star with a large proper motion can
  be 10″ or more from its J2000 position, so cone searches on such stars need a margin.

## TESS light curves
- **Pixels are 21″.** Neighbours blend in, which `Rcont` in the TIC measures: the flux
  from neighbours over the star's own flux.
- **Ready-made light curves from the full-frame images.**
  - QLP and TESS-SPOC reach Tmag ≈ 13.5; TGLC and GSFC-ELEANOR-LITE reach Tmag ≈ 16.
  - Fainter stars are mostly too faint for a useful transit search.
  - The tools rate extraction as good (Tmag ≤ 13.5, Rcont < 0.2), possible (Tmag ≤ 16,
    Rcont < 1) or poor.
- **Full-frame cadence depends on the sector:** 30 min (sectors 1–26), 10 min (27–55),
  then 200 s. 2-min and 20-s light curves exist only for stars that were proposed as
  targets.
- **Short-cadence candidates** (stars worth proposing) default to Tmag < 13, log g ≥ 4,
  R ≤ 1.5 R☉ and Rcont ≤ 0.1, the mission's own priorities: small, bright,
  uncontaminated dwarfs. Future TESS pointings are not checked.
- The HLSP pipelines at MAST include QLP, TESS-SPOC, TGLC, GSFC-ELEANOR-LITE, TASOC,
  CDIPS, PATHOS, DIAMANTE, T16, TARS and TEQUILA.

## Default decisions and what to tell the user
| Situation | Default | Tell the user |
|---|---|---|
| "Planets here" | `exoplanet_hosts` | Say how many planets have measured masses, and how many are estimated or minimum masses. |
| A planet's mass or radius | The exoplanet agent | Relay its checked answer; it cites the paper or the archive for each value. |
| "Habitable", "has an atmosphere" and other vague constraints | The exoplanet agent asks for a definition first | Pass the user's choice back as `criteria`. |
| Light curves for stars in the field | The exoplanet agent's light-curve tools | Give the rating and its reason (Tmag, contamination, sectors). |

## Not yet verified
- How often the TOI table's dispositions are updated relative to the archive's weekly
  releases.
