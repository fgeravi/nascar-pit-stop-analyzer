# NASCAR Pit Stop Analyzer

A compact Python analytics project that downloads and analyzes NASCAR Xfinity pit-stop data. It ranks pit crews and drivers, compares stop strategies, flags unusual stops, measures position change, evaluates pit-stop consistency, and creates three portfolio-ready visuals.


## Data source

The project is configured for this NASCAR JSON feed:

`https://cf.nascar.com/cacher/live/series_2/5314/live-pit-data.json`



## What the project produces

- Headline race and pit-stop metrics
- Driver-level performance rankings
- Stop-type comparisons
- Driver pit-stop consistency analysis
- IQR-based long-stop outlier detection
- CSV and JSON reports
- `driver_consistency.csv`
- `driver_average_pit_stops.png`
- `driver_pit_stop_consistency.png`
- `duration_vs_positions.png`

