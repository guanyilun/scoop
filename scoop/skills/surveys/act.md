---
name: act
description: Atacama Cosmology Telescope (ACT) maps and the ACT+Planck Compton-y
  maps, for millimetre emission, SZ clusters and the CMB around a field. Which
  copy to look at (CDS HiPS) and which to measure (the official LAMBDA files).
used_by: [imaging, sz, data agent]
status: draft
sources_checked: 2026-10-22 (CDS MOC server records; LAMBDA DR6.02 product pages)
---

# ACT maps and Compton-y

## What's here
- **Quick-look copies at CDS** (HiPS, for the map and `sky_image`; `fits_cutout` works on them):
  - `CDS/P/ACT-PLANCK/DR4DR6/f090`, `f150`, `f220`: ACT DR4 + DR6 + Planck coadds,
    from S. Naess (arXiv:2503.14451). Also `Color_CMB`, `Color_MW`,
    `f090/PointSource` and low-resolution `map_healpix_{Q,U,E,B}`.
  - `CDS/P/ACT/Planck/DR6/Compton-y`: the ACT DR6 + Planck y map of Coulton+ 2023
    (arXiv:2307.01258; LAMBDA `ilc_actplanck_ymap.fits`).
  - `CDS/P/ACT/DR4/*`, `CDS/P/ACT/DR5/*`, `CDS/P/ACT_Planck/DR{4,5}/*`: older, HiPS
    cubes; hips2fits refuses them ("Unknown HiPS").
  - `ov-gso/P/ACT/Planck/f090,f150,f220`: a separate ACT+Planck build by IRAP/CADE.
- **Official files at LAMBDA** (for measurements). The download pages list every file:
  - DR6.02 maps (Naess+ 2025): `https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_maps_coadd_get.html`.
    Files are `https://lambda.gsfc.nasa.gov/data/act/maps/published/{type}_coadd_AA_{night|daynight}_{f090|f150|f220}_{product}.fits`,
    where type is `act_dr6.02`, `act-planck_dr6.02`, `act_dr4dr6` or `act-planck_dr4dr6`
    and product is `map`, `map_srcfree`, `ivar`, or a `_healpix` version.
    Per-array maps, null tests and ancillary files have their own `act_dr6.02_maps_*_get.html` pages.
  - DR6.02 needlet-ILC maps, made from the ACT **DR6v4** maps and Planck with the method of Coulton+ 2024:
    `https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/act_dr6.02_nilc_get.html`.
    Files are `https://lambda.gsfc.nasa.gov/data/act/nilc/published/act-planck_dr6.02_nilc_{ComptonY|blackbody_T|blackbody_E}[_deproj_{components}_{beta}_{T}].fits`.
    There are 61 Compton-y variants: no deprojection, or CIB deprojected (`cib`, and optionally
    `cibdBeta` and/or `cibdT`) for beta 1.0–1.8 and T 10.7 or 24.0 K. Masks are `footprint_mask.fits`,
    `ilc_inpaint_mask.fits` and `ilc_subtracted_mask.fits`. All maps have a 1.6′ Gaussian beam.
  - The older Coulton+ 2023 y map: `https://lambda.gsfc.nasa.gov/product/act/actadv_dr6_compton_maps_get.html`.

## Gotchas
- The CDS copies are resampled twice: once onto HEALPix tiles, and again by hips2fits's
  reprojection. Their PNG stretch also saturates. Use them for seeing, not for fluxes, y
  values, profiles or stacking.
- CDS does not record the map version of its ACT copies. Its Compton-y is the 2023 map,
  not one of the DR6.02 NILC maps.
- The LAMBDA files are whole-footprint CAR maps: about 1.8 GB per NILC map and 5.3 GB per
  coadd. Download each once into a cache directory, never per question, and confirm with
  the user before downloading. Then cut out the field in `run_kernel` with pixell
  (`enmap.read_map(path, box=...)` reads only that box), or with astropy.
- LAMBDA says the NILC y maps carry a lot of residual CIB. Compare the plain ILC with
  CIB-deprojected maps (varying beta, then adding dBeta, then dT) before trusting an
  SZ signal. Deprojecting costs resolution: lmax is about 11000 with 2 deprojections
  and about 4000 with 3.
- Maps follow the IAU polarization convention (`POLCCONV='IAU'`).

## Default decisions and what to tell the user
| Situation | Default | Tell the user |
|---|---|---|
| "Show ACT / SZ here" | Background `CDS/P/ACT-PLANCK/DR4DR6/f150` or `.../Compton-y` | "This is CDS's quick-look copy of the ACT map; values are display-stretched." |
| A measurement on ACT data | Official LAMBDA file, cut out with pixell | "Measured on LAMBDA's act-planck_dr6.02_… map (DR6.02), not the CDS copy." |
| A y measurement | `act-planck_dr6.02_nilc_ComptonY.fits`, plus a CIB-deprojected variant as a check | Name both files and the difference between them. |
| The user has internal ACT/SO maps | Their paths | Use those, and record the version they name. |

## Not yet verified
- Downloading a full LAMBDA file and cutting it with pixell inside SCOOP's kernel.
- ACT's preferred acknowledgement text.
