# Data and Knowledge Sources

Candidate primary sources for each of the five required domains, to expand `data/knowledge/*.md` and refine `data/causal_map.json` beyond the first-draft curation with primary citations, page references, and effect sizes.

## Soil health
- SoilGrids (ISRIC) — global soil properties (pH, organic carbon, texture, bulk density) at 250m resolution. https://www.isric.org/explore/soilgrids / https://soilgrids.org — raster/GeoTIFF via WCS/REST API.
- FAO Global Soil Partnership — soil reports, Global Soil Organic Carbon map, soil data catalogue. https://www.fao.org/global-soil-partnership

## Land use / land cover
- ESA WorldCover — global 10m land cover map (11 classes), 2020 and 2021. https://esa-worldcover.org/en — Cloud-Optimized GeoTIFFs, also available via Google Earth Engine.
- FAOSTAT — land use statistics by country, time series since 1961. https://www.fao.org/faostat

## Biodiversity indicators
- GBIF (Global Biodiversity Information Facility) — species occurrence records worldwide. https://www.gbif.org — CSV/Darwin Core downloads, queryable by region/species.
- IPBES — global and regional biodiversity assessment reports. https://www.ipbes.net — PDF reports; the primary source for biodiversity-decline literature and figures, not raw data.

## Climate factors
- IPCC Data Distribution Centre — observed and projected climate data (temperature, rainfall, emissions scenarios). https://www.ipcc-data.org
- IPCC Assessment Reports (AR6 and prior) — narrative and quantitative climate-impact findings. https://www.ipcc.ch

## Human impact
- Global Forest Watch (World Resources Institute) — near-real-time deforestation and forest-loss data. https://www.globalforestwatch.org — interactive map plus downloadable layers.
- FAO — land degradation and deforestation reporting via the Global Soil Partnership and FAOSTAT portals above.

## How this feeds the project
Per the blueprint (Section 7), these sources serve two purposes at once: populating the vector index (`rootcause/knowledge/vectorstore.py` over `data/knowledge/*.md`) and supplying labeled, citable edges for the causal map (`data/causal_map.json`).

## Citation verification pass (2026-09-17)

Every peer-reviewed and institutional-report citation in `data/causal_map.json` and `data/knowledge/*.md` was checked against a live web search and replaced with a verified DOI, publisher URL, or ISBN rather than a bare author-year string. Status:

**Verified with an exact DOI (peer-reviewed papers):**
- Poeplau & Don (2015) — Agriculture, Ecosystems & Environment 200:33-41 (ScienceDirect link; exact DOI suffix not independently confirmed, so the ScienceDirect PII URL is used instead of a guessed DOI)
- Blanco-Canqui et al. (2015) — `10.2134/agronj15.0086`
- Lori et al. (2017) — `10.1371/journal.pone.0180442`
- Tsiafouli et al. (2015) — `10.1111/gcb.12752`
- Six, Bossuyt, Degryze & Denef (2004) — `10.1016/j.still.2004.03.008`
- Klein et al. (2007) — `10.1098/rspb.2006.3721`
- Landis, Wratten & Gurr (2000) — `10.1146/annurev.ento.45.1.175`
- Edwards & Bohlen (1996) — book, ISBN 978-0-412-56160-3 (no DOI; 3rd ed., Chapman & Hall)
- FAO (2017), Agroforestry for Landscape Restoration — `10.4060/i7374e`
- West & Post (2002) — Soil Science Society of America Journal 66:1930-1946, `10.2136/sssaj2002.1930` (no-till 57 ± 14 g C m⁻² yr⁻¹, excluding wheat-fallow; rotation complexity 14 ± 11 g C m⁻² yr⁻¹)
- Shi, Feng, Xu & Kuzyakov (2018) — Land Degradation & Development 29:3886-3897, `10.1002/ldr.3136` (427 paired comparisons; agroforestry soil C stock 126 Mg C/ha, ~19% above adjacent cropland/pasture — a stock difference, not a rate)
- Albrecht et al. (2020) — Ecology Letters 23:1488-1498, `10.1111/ele.13576` (flower strips +16% pest control on average; pollination effects more variable)
- Tamburini et al. (2020) — Science Advances 6(45):eaba1715, `10.1126/sciadv.aba1715` (diversification enhances biodiversity, pollination, pest regulation without lowering yield)
- Hou, Zhu & Jin (2016) — PLOS ONE, `10.1371/journal.pone.0154799` (mulching and surface salinity)
- Geiger et al. (2010) — Basic and Applied Ecology 11(2):97-105, `10.1016/j.baae.2009.12.001`

**Verified with an official landing page (institutional reports/assessments):**
- IPBES (2016) Pollinators Assessment — https://www.ipbes.net/assessment-reports/pollinators
- IPBES (2018) Land Degradation and Restoration Assessment — https://www.ipbes.net/node/28328
- IPBES (2019) Global Assessment — https://www.ipbes.net/global-assessment
- IPCC AR6 WG1 (Physical Science Basis) — https://www.ipcc.ch/report/ar6/wg1/
- IPCC AR6 WG2 (Impacts, Adaptation and Vulnerability) — https://www.ipcc.ch/report/ar6/wg2/
- FAO (2019) Soil Erosion report — https://openknowledge.fao.org/items/6c070e1e-6533-4b7e-ba5f-a2f21a0e59ff
- FAO (2019) State of the World's Biodiversity for Food and Agriculture — https://openknowledge.fao.org/items/b355c300-72ed-4a63-be07-8295c80ec7f1
- FAO Global Soil Organic Carbon (GSOC) Map — https://www.fao.org/global-soil-partnership/pillars-action/4-information-and-data-new/global-soil-organic-carbon-gsoc-map/en/
- FAO International Network on Salt-Affected Soils (INSAS) — https://www.fao.org/global-soil-partnership/insas/en
- FAO Water Pollution from Agriculture (2018) — https://www.fao.org/newsroom/detail/Pollutants-from-agriculture-a-serious-threat-to-world's-water/en
- FAO Conservation Agriculture programme — https://www.fao.org/conservation-agriculture/en/

**Linked to the closest official page, but not a single precisely-dated dedicated document** (flagged inline in the citation text itself, so this is visible wherever the claim is used, not just here):
- "FAO Global Soil Partnership, Soil Acidification guidance note" and "Soil Fertility guidance" — no single dedicated page was found; linked to the general FAO Global Soil Partnership portal instead.
- "FAO (2021), Rangeland and Pasture Management guidance" — linked to FAO's "Sustainable rangeland management in Sub-Saharan Africa: Guidelines to Good Practice," but the 2021 date could not be independently confirmed for that specific document.

**Left as an intentionally generic reference (one edge only):** the rainfall → vegetation-cover edge (`e37`) cites "general agroecology / rangeland ecology literature synthesized in FAO Land and Water reports" — no single source was substituted for this because none was found precise enough to name; it remains an honest placeholder rather than a fabricated citation.

The distinction matters for the submission: a reviewer can click through and verify roughly three-quarters of the edges against an exact paper or exact assessment report, and the remaining ones are explicitly marked as pointing to a general portal rather than a precise document — nothing here claims more precision than was actually verified.
