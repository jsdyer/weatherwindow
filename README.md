# Weather Window

A live Canadian weather board for current conditions, text and hourly forecasts, regional air quality, official alert areas and personally chosen outdoor limits.

Use https://coolcode.ca/weatherwindow/

<!-- coolcode:guide -->
Search any listed Canadian forecast place, an ECCC place ID, or latitude, longitude; save places on this browser and set your temperature, wind and precipitation-probability limits. Matching hours are weather preferences, not an all-clear: read the separately dated official alerts and AQHI observations/forecast periods, and check the named station's distance. Missing inputs never count as a matching window.
<!-- /coolcode:guide -->

## What the board means

- The directory contains every ECCC City Page Weather place returned by the national source (844 in the verified initial capture). The city API is explicitly experimental. Coordinates select the nearest forecast place and show its distance; observations name the actual station, which can differ from the forecast place. This is not a street-level forecast.
- Observations, text forecasts and hourly forecasts retain their separate official times. The source's hourly issue timestamp can occasionally be future-dated; it remains visible with a warning rather than being replaced with retrieval time. Hourly times are shown in the visitor's device timezone.
- AQHI observations request `latest=true`, then choose the nearest reporting location within the configured distance. AQHI forecast periods are a different source: they request that location, `aqhi_type=AQHI-Forecast-Period`, and `sortby=-publication_datetime`; the newest returned publication is selected. Applying `latest=true` to the forecast source incorrectly returns no data. Readings remain numeric source values, not interpolated values for the chosen address. Quebec observations are not published in this federal feed.
- Alerts retain official polygon geometry, publication/expiration times, type, colour and English text. A point-in-polygon test, including polygon holes, determines which active areas contain the selected point. The map also shows nearby alert areas. An empty successful response and a failed request are visibly different.
- Matching hours use temperature, sustained wind (and gusts when present), and precipitation probability. They do not forecast AQHI from an observation and do not treat an absence of displayed alerts as a safety certification. Missing hourly inputs stay unknown.
- Source failures retain successful values for the same selected place with their original source and retrieval times. Switching places clears the previous place's values. Nothing auto-refreshes without a visitor action. Press **Refresh sources** to check again.

## Sources and privacy

[ECCC City Page Weather](https://eccc-msc.github.io/open-data/msc-data/citypage-weather/readme_citypageweather_en/), [AQHI](https://eccc-msc.github.io/open-data/msc-data/aqhi/readme_aqhi_en/) and [weather alerts](https://eccc-msc.github.io/open-data/msc-data/alerts/readme_alerts-geomet_en/) are accessed directly through the public CORS-enabled `api.weather.gc.ca` API. No key or Worker gateway is needed. API schema/availability changes are checked daily; the board exposes a place's official weather.gc.ca link as a fallback. An API failure is not silently replaced with a different model.

Choosing a place sends its ID/coordinates to ECCC. Map tiles come from OpenStreetMap for the visible area. Browser location is requested only after the visitor presses **Use my location**. Places and limits are saved in `coolcode:weatherwindow:places` and `coolcode:weatherwindow:limits` local storage, not cookies or a server account. **Clear saved places** removes the saved-place list; limits can be changed in the form. Private browsing or clearing site storage removes preferences. The shared CoolCode counter records aggregate opens only.

Application code is MIT licensed; upstream data and the vendored map library keep their original terms. ECCC data is attributed under its [data licence](https://eccc-msc.github.io/open-data/licence/readme_en/). The map attributes OpenStreetMap contributors. Leaflet 1.9.4 is vendored only for the interactive map; its licence is in `web/vendor/LICENSE`. No build or production npm dependency is needed.

## Expand or customize

`web/config.json` controls starting place/preset IDs, thresholds, request timeout, pagination cap, observation staleness (minutes), and suggested AQHI distance (km). Presets are shortcuts, not coverage restrictions. Visitors can choose any directory place or valid Canadian coordinates. For example, add `on-83` to `presets` to add Deep River without changing validation or count logic. IDs and names can be found in `web/data/catalog.json`; add no invented forecast places to the directory.

Run `python3 scripts/refresh.py` to fetch the complete directory and validate live city weather, AQHI observation, AQHI forecast and alert schemas plus CORS. It writes `web/data/catalog.json` and `web/data/source-health.json` only after all checks pass. These dates describe directory/API checks, not fresh weather measurements. The app fetches weather on demand.

**Browser tool · Check and publish** (`pages.yml`) refreshes these source checks daily at **09:23 UTC**, and on manual dispatch. Scheduled failures keep the previous deployment and its dates. Code pushes build offline from retained directory data; to adopt new source metadata, run the collector or manually dispatch the workflow, then test and push/deploy. A separate weekly allowlisted guard helps restore inactivity-disabled workflows. The hub's independent refresh watchdog must register `pages.yml` with the daily cadence and `data/source-health.json` → `checked_at` freshness probe. Source-check step: **Check ECCC sources and refresh place directory**.

Supported direct links:

- `https://coolcode.ca/weatherwindow/?place=ns-19`
- `https://coolcode.ca/weatherwindow/?lat=44.65&lon=-63.6`

Build and verify:

```sh
node --test tests/*.test.mjs
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 tests/browser_smoke.py
```

The build is offline and creates relative, content-versioned assets in `dist/`; do not commit `dist/`. Browser checks run under Chrome in CI at the project subpath with real-shape fixtures, test saved places, unknown values, source failure retention and mobile overflow. CI publishes successful `main` builds through GitHub Pages. Enable GitHub Actions as the Pages source. Follow the hub [tool lifecycle](https://github.com/jsdyer/jsdyer.github.io/blob/main/docs/tool-lifecycle.md) for catalogue, guide, watchdog, audit, Worker ID and sitemap integration. Weather Window requires no secret or new API route.
