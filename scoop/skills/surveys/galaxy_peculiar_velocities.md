---
name: galaxy_peculiar_velocities
description: Peculiar velocities of galaxies and groups beyond the Local Group, from
  redshift-independent distances (Cosmicflows-4, 6dFGS and SDSS Fundamental Plane,
  DESI DR1, Pantheon+ supernovae) and, statistically, from the kinematic SZ effect.
  Load for any question about a galaxy's or cluster's peculiar velocity, bulk
  flows, or the velocity field around a field.
used_by: [cosmology, data agent]
status: draft
sources_checked: 2026-10-22 (VizieR ReadMe files and TAP queries; ADS abstracts;
  Zenodo records; DESI DR1 public VAC listing)
---

# Galaxy peculiar velocities

A peculiar velocity is what is left of a galaxy's redshift after the Hubble flow:
roughly v_pec ≈ cz − H0·d. It needs a **distance that doesn't come from the
redshift**: Tully-Fisher (spirals), the Fundamental Plane (ellipticals), type Ia or II
supernovae, surface brightness fluctuations, or TRGB and Cepheids nearby. For the Milky
Way's satellites and the Local Group, use the proper-motion skill
(astrometry/proper_motions) instead.

## What's here

| Catalogue | What | Where |
|---|---|---|
| **Cosmicflows-4** (Tully+ 2023, 2023ApJ...944...94T) | 55,877 galaxies in 38,065 groups, 8 distance methods merged by MCMC; all-sky to cz ≈ 30,000 km/s | VizieR `J/ApJ/944/94/table2` (galaxies: `DM`, `e_DM` and one column per method, `Vcmb`, `PGC`, `1PGC` group) and `J/ApJ/944/94/groups` (groups: `DMzp`, `e_DMzp`, `Dist`, `V3k`, **`Vpec`**, plus `Vpds` and `Vpwf` from two other estimators); more at the Extragalactic Distance Database (edd.ifa.hawaii.edu) |
| **6dFGS peculiar velocities** (Springob+ 2014, 2014MNRAS.445.2677S) | 8,885 southern early-type galaxies, Fundamental Plane, z < 0.055 | VizieR `J/MNRAS/445/2677/table1`: `czgal` (CMB frame), `log(Dz/DH)`, `e_log(Dz/DH)` and the skew `alpha` of its distribution, group ids |
| **SDSS peculiar velocities** (Howlett+ 2022, 2022MNRAS.515..953H) | 34,059 early-type galaxies, Fundamental Plane, calibrated to Cosmicflows-3's zero point | Not on VizieR. Zenodo record 6640513: `SDSS_PV_public.dat` (20 MB), `data_description.pdf`, randoms (284 MB) and 2048 mocks (10.6 GB, `mocks.tar.gz`) |
| **Pantheon+ supernova redshifts and PVs** (Carr+ 2022, 2022PASA...39...46C) | 2,287 SN Ia rows with heliocentric, CMB-frame and corrected redshifts | VizieR `J/other/PASA/39.46/table2`: `zhel`, `zcmb`, `zHD`, `vpec`, `e_vpec`, host-group values (`vpecG`) |
| **DESI DR1 PV survey** | Fundamental Plane distances and PVs for 98,292 early-type galaxies (Ross+ 2026, 2026PASA...43..114R); Tully-Fisher for 10,262 spirals (arXiv:2512.03227) | **Not public yet** (checked 2026-10-22): the FP paper says the data will be a DESI value-added catalogue, and the DR1 public VAC list (data.desi.lbl.gov/public/dr1/vac/dr1/) has no PV entry. The Zenodo record linked from that paper (17784593) only holds a README. |
| DESI PV target selection (Saulder+ 2023) | Which galaxies DESI targeted for PVs, not velocities | VizieR `J/MNRAS/525/1106` |
| Older: Cosmicflows-2 and -3, Mark III, SFI++, 2MTF, 6dFGS FP data | Superseded by the rows above for most uses | VizieR (`J/AJ/146/86`, `J/AJ/152/50`, `VII/198`, `J/ApJS/172/599`, ...) |

**The kinematic SZ (kSZ) effect** measures velocities statistically, not per galaxy:
CMB temperature shifts proportional to the gas's line-of-sight velocity, detected by
stacking many galaxies. With ACT, for example: the pairwise kSZ with SDSS DR15
(2021PhRvD.104d3502C), velocity reconstruction with DESI LRGs (2025JCAP...05..057M),
and gas profiles from DESI Y1 and ACT (2025PhRvD.112j3512R). For the CMB maps, see
the skill surveys/act. A kSZ measurement is a separate analysis; no catalogue of
per-object kSZ velocities exists. The cutout-and-stack mechanics are those of ACT's y-map
stacking notebook (surveys/act, Recipes), applied to the CMB temperature maps with a
velocity or pairwise weighting. The kSZ papers above give the estimators and their
filtering; the plain y-map stack is not enough on its own, because the kSZ signal is
far smaller than primary-CMB fluctuations.

## Gotchas
- **Errors are large and grow with distance.** A distance-modulus error σ_μ gives
  σ_v ≈ (ln 10 / 5) · cz · σ_μ ≈ 0.46 · cz · σ_μ. Near Coma, live query: the Coma group
  (263 galaxies, e_DMzp = 0.025 mag, V3k = 7,193 km/s) has Vpec = 85 km/s, about
  ±85 km/s; single galaxies behind it at cz ≈ 20,000 km/s with e_DM ≈ 0.5 mag carry
  errors of about 4,600 km/s, so a listed Vpec of −5,825 km/s is noise. Report errors
  always, and prefer group values.
- **Cosmicflows-4's galaxy table has no velocity column**, and **its group table has
  Vpec but no error on it**. Derive the error from `e_DMzp` and `V3k` with the formula
  above, and say that you did.
- **The zero point is H0.** CF4's distances are compatible with H0 = 74.6 km/s/Mpc
  (from its abstract). Every PV shifts by about cz·ΔH0/H0 if H0 changes: 1 % at
  10,000 km/s is 100 km/s for every galaxy. Use one catalogue's own scale throughout;
  never mix distances calibrated on different scales.
- **Use the right estimator.** v = cz − H0·d is biased because distance errors are
  log-normal. Catalogues therefore give the log distance ratio η = log10(Dz/DH)
  (6dFGS), or PVs from the Watkins & Feldman (2015) estimator,
  v ≈ ln(10) · cz/(1+z) · η (CF4's `Vpwf`). A positive η means the galaxy is nearer
  than its redshift implies, so it is moving away from us. Average in η, not in v.
  6dFGS's η is skewed (`alpha`).
- **Frames.** Use CMB-frame redshifts (`Vcmb`, `V3k`, `czgal`, `zcmb`), not
  heliocentric ones.
- **Selection biases** (Malmquist bias from distance errors, and inhomogeneous
  Malmquist bias from structure along the line of sight) are handled differently in
  each catalogue. Read each paper's treatment before combining catalogues. Combining
  catalogues needs a common zero point.
- **Pantheon+ `vpec` values are model corrections** (the paper's improved
  peculiar-velocity model), not measurements from SN distances. Don't treat them as
  independent PV measurements.
- **Overlap is not independence.** The same galaxy or group can appear in CF4, 6dFGS
  and SDSS; CF4 includes earlier 6dFGS and SDSS distances.

## Default decisions and what to tell the user
| Situation | Default | Tell the user |
|---|---|---|
| "Peculiar velocity of this galaxy or cluster" | CF4 groups first (cone on `J/ApJ/944/94/groups`), then the galaxy table | "Cosmicflows-4 gives Vpec = … ± … km/s for the group (N galaxies; error from e_DMzp); distances on CF4's H0 = 74.6 scale." |
| Southern early-type galaxies at z < 0.055 | 6dFGS η, converted with Watkins & Feldman | Give η ± error and the converted velocity, with the note that the conversion is approximate. |
| SDSS footprint, early types | SDSS PV catalogue (Zenodo, 20 MB, needs the user's OK before downloading) | Say it is calibrated to Cosmicflows-3's zero point. |
| "Bulk flow / velocity field here" | Group-averaged PVs in the region, with errors | A bulk flow needs many objects and a model of the errors; offer to set it up in run_kernel rather than quoting a mean. |
| DESI PVs requested | Not available yet | "DESI DR1 PVs are published (Ross+ 2026) but the catalogue isn't public yet." |
| kSZ velocities requested | Explain it's statistical | Point to the papers above and the ACT maps; offer a stacking analysis in run_kernel as a project, not a lookup. |

## Not yet verified
- CF4's notes (5)–(7) on DMzp, fV3k and Hi (the ReadMe cut off before them), and
  exactly how the "ramp" Vpec (Equation 11) blends Vpds and Vpwf.
- The columns and units of `SDSS_PV_public.dat` (read `data_description.pdf`).
- When the DESI DR1 PV value-added catalogue is released, and its columns.
