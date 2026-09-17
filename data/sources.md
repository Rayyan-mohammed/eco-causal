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
Per the blueprint (Section 7), these sources serve two purposes at once: populating the vector index (`rootcause/knowledge/vectorstore.py` over `data/knowledge/*.md`) and supplying labeled, citable edges for the causal map (`data/causal_map.json`). The current knowledge base and causal map are a first-draft, hand-curated version from well-established literature; replacing the citation strings with exact primary-source page/DOI references pulled from these portals is the natural next step before the submission deadline.
