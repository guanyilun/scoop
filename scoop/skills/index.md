# SCOOP skills index

Every agent's instructions list these skills by name and description; agents load only
the ones a request needs (read_skill). This index groups them by topic.
Each skill describes what a source holds (and doesn't), how to check coverage
and cost before downloading, how to query it, its gotchas, the default
decisions an agent makes and what it tells the user about them, and how to
cite it.

Whatever skill is used, every record an agent returns must carry its
provenance (archive, native ID, position, footprint, query, access URL) so the
evaluation checks in [`evaluation/`](../../evaluation/README.md) can verify it against the
archive.

## Surveys and archives (`surveys/`)

| Skill | Use it for |
|---|---|
| [gaia](surveys/gaia.md) | Astrometry (positions, parallaxes, proper motions), G/BP/RP photometry, radial velocities, XP/RVS spectra, Gaia QSO and galaxy candidates |
| [mast_hst_jwst](surveys/mast_hst_jwst.md) | HST and JWST images and spectra, footprints, epochs and baselines, exclusive-access and planned observations, Hubble Source Catalog, HAP mosaics, HLSPs |
| [cadc_cfht](surveys/cadc_cfht.md) | CFHT observations (MegaCam images etc.) at CADC, as footprints via ObsCore (draft) |
| [act](surveys/act.md) | ACT maps (90/150/220 GHz) and ACT+Planck Compton-y: CDS quick-look copies vs the official DR6.02 LAMBDA files, NILC y-map variants (draft) |
| [lamost](surveys/lamost.md) | LAMOST spectroscopic catalogs via VizieR, up to DR11 (draft) |
| [sdss_spectra](surveys/sdss_spectra.md) | SDSS optical and APOGEE infrared spectra (SDSS-I through V, DR20), MaNGA, redshifts and classifications |

## Astrometry (`astrometry/`)

| Skill | Use it for |
|---|---|
| [proper_motions](astrometry/proper_motions.md) | Where existing proper motions are (LVDB for galaxies and clusters, Gaia for stars, none beyond the Local Group) and whether better-than-Gaia ones could be measured |

## Literature (`literature/`)

| Skill | Use it for |
|---|---|
| [stsci_proposals](literature/stsci_proposals.md) | The HST and JWST programs behind observations in a region: why they were proposed, status, and what came of them |

## Writing new skills (`meta/`)

| Skill | Use it for |
|---|---|
| [new_survey_skill](meta/new_survey_skill.md) | Writing a skill for a survey or archive that isn't listed here (or whose release changed), including facilities whose data aren't public yet |
| [dataset_scout](meta/dataset_scout.md) | The monthly scan for datasets SCOOP is missing or has gone stale on: running it, reviewing what it produced, and changing what it looks for (`python -m scoop.scout`) |

## To write

Data-type skills (`imaging/`, `spectra/`, `astrometry/`, `photometry/`) giving
the context for choosing between surveys, and survey skills for Euclid, DESI,
the Local Volume Database, galstreams, QSO catalogs, NED and SIMBAD.
