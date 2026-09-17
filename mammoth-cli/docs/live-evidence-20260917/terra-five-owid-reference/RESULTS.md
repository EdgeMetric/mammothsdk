# Terra five-source OWID CLI reference

Run date: 2026-09-17. Scope: workspace 4, project 3, with only datasets
created by this run. This is a Terra-operated reference workflow, not an
autonomous-agent qualification.

## Environment and resolver regression

The initial imports and contract discovery used the published `mammoth-cli`
1.1.10 CLI. After the wrong-parent dataview-resolution defect was fixed in
SDK commit `f980b65`, the continuation used an isolated editable local CLI
(`mammoth-cli` 1.1.11) whose `mammoth.__file__` resolved to this checkout.

With multiple owned datasets present, bare-parent operations on GDP view 46
resolved to its real parent dataset 29 and succeeded:

- `view get 46`
- `view preview 46`
- `view export csv 46`

This directly contrasts with R6, where bare view 34 was first probed below
its actual parent and received a wrong-parent 403. Explicit parent IDs remain
the safest invocation form until a released CLI contains the resolver fix.

## Verified workflow (at time of verification)

Owned source datasets were population 28, GDP 29, life expectancy 30,
internet use 31, and CO2-per-capita 33. Accidental duplicate imports 32 and
34 were also owned by this run.

Views 45--49 were created under their exact respective parents. The typed CLI
workflow was:

1. `view transform discard-duplicates` on population view 45 (future 113,
   pipeline later `ready`).
2. Typed GDP-to-population `INNER` join on `Code` and `Year` (future 115),
   followed by typed `GDP / Population` math to numeric `GDP per capita`
   (future 119).
3. Typed `LEFT` joins of life expectancy (future 122), internet use (124),
   and CO2 per capita (126), each on the same display-name keys.

Remote preview of view 46 then contained all nine columns:

`Entity, Code, Year, GDP, Population, GDP per capita, Life expectancy,
Internet use, CO2 per capita`.

For Afghanistan in 2005 it returned GDP `46566715049`, population
`24404575`, GDP per capita `1908.114157`, life expectancy `58.2468`, internet
use `1.224148`, and CO2 per capita `0.077424`.

`dashboard create-blank` created dashboard 47 with source 46; `dashboard get
47` verified its title, source, and completed autosync. The generic
`dashboard source list` route still returned structured HTTP 500. The legacy
`dashboard create` route is retired (409) and was not used for this result.

The local CSV export made after the GDP-per-capita metric was verified at
`/tmp/terra-owid-gdp-per-capita.csv`: 354,766 bytes, SHA-256
`34129e5ac05d78f50b34a162137df0c5f18c0faca5f24d1f833a88d33a53080a`.
Its header and first two rows were:

```text
Entity,Code,Year,GDP,Population,GDP per capita
Afghanistan,AFG,2005,46566715049,24404575,1908.114157
Afghanistan,AFG,2008,58036781460,26482631,2191.503611
```

## Current retained deliverable and limitations

The dashboard was deleted during an initial cleanup attempt, then the user
requested an inspectable deliverable. No new imports were made. The three
removed typed joins were reapplied as tasks 8--10, with the pipeline returning
`ready` after each. The current active sources are 28, 29, 30, 31, and 33;
view 46 again has the nine-column preview above.

Dashboard 48 is the current active draft, titled `Terra OWID five-source
reference`, with source 46 and completed autosync. Its direct `dashboard get`
readback succeeded. The final current CSV export is
`/tmp/terra-owid-five-source-final.csv`: 508,309 bytes, SHA-256
`1e0c8b5356412adfd42990084e70fc02c9fbdd8a79d46529c032f28469f07028`.
Its header and first two rows are:

```text
Entity,Code,Year,GDP,Population,GDP per capita,Life expectancy,Internet use,CO2 per capita
Afghanistan,AFG,2005,46566715049,24404575,1908.114157,58.2468,1.224148,0.077424
Afghanistan,AFG,2008,58036781460,26482631,2191.503611,59.7081,1.84,0.160652
```

The interrupted cleanup still provides a useful limitation: downstream
dataset 29 was first trashed before upstream 28, and the backend correctly
returned `TRASH_DEPENDENT_BLOCK` for 28. Owned datasets were restored before
the current joins were reapplied. No cleanup is pending or authorized for the
active deliverable.

Product follow-ups:

- Release the parent-resolution fix from `f980b65`; until then a bare view ID
  can be misrouted after a wrong-parent backend 403.
- Document dependency-aware cleanup ordering: remove downstream pipeline tasks
  before trashing upstream sources. A successful downstream trash does not
  remove its source dependency.
- Treat `dashboard source list` HTTP 500 as a backend limitation; dashboard
  creation and direct dashboard readback did succeed.
