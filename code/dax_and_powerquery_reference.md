# DAX & Power Query Reference

These are simplified, generalized versions of the measures and transformation
logic used in the dashboard, rewritten with generic table/column names. They
illustrate the statistical and data-modeling approach rather than reproducing
the original implementation verbatim.

Assumed generic schema for these examples:

- **`Monitoring`** (fact table): `NutrientName`, `Value`, `SpecMin`, `SpecMax`, `SpecTarget`, `Date`, `IncludeInStats`
- **`DateTable`** (dimension): standard date dimension joined on `Date`

---

## 1. Core summary statistics

```dax
Avg Value =
CALCULATE(
    AVERAGE(Monitoring[Value]),
    Monitoring[IncludeInStats] = 1
)

Std Dev (Cleaned) =
CALCULATE(
    STDEV.P(Monitoring[Value]),
    Monitoring[IncludeInStats] = 1
)

RSD % =
DIVIDE([Std Dev (Cleaned)], [Avg Value], BLANK()) * 100

Recovery % =
DIVIDE([Avg Value], AVERAGE(Monitoring[SpecTarget]), BLANK()) * 100

Deviation % =
DIVIDE(
    [Avg Value] - AVERAGE(Monitoring[SpecTarget]),
    AVERAGE(Monitoring[SpecTarget]),
    BLANK()
) * 100
```

## 2. Statistically-derived control limits vs. fixed specification

```dax
LCL (Statistical) = [Avg Value] - (2 * [Std Dev (Cleaned)])
UCL (Statistical) = [Avg Value] + (2 * [Std Dev (Cleaned)])

Spec Review Flag =
VAR NewLCL = [LCL (Statistical)]
VAR NewUCL = [UCL (Statistical)]
VAR SpecMin = AVERAGE(Monitoring[SpecMin])
VAR SpecMax = AVERAGE(Monitoring[SpecMax])
VAR N = CALCULATE(COUNTROWS(Monitoring), Monitoring[IncludeInStats] = 1)
VAR ThresholdPct = IF(N < 20, 0.20, 0.10)
RETURN
    IF(
        ABS(NewLCL - SpecMin) / SpecMin > ThresholdPct
            || ABS(NewUCL - SpecMax) / SpecMax > ThresholdPct,
        "Review spec",
        "OK"
    )
```

## 3. Outlier detection — standard Z-score and modified Z-score

```dax
Z-Score =
VAR Nutrient = Monitoring[NutrientName]
VAR MeanValue =
    CALCULATE(AVERAGE(Monitoring[Value]), ALLEXCEPT(Monitoring, Monitoring[NutrientName]))
VAR StdDevValue =
    CALCULATE(STDEV.P(Monitoring[Value]), ALLEXCEPT(Monitoring, Monitoring[NutrientName]))
RETURN
    DIVIDE(Monitoring[Value] - MeanValue, StdDevValue)

Is Outlier (Z) = IF(ABS([Z-Score]) > 3, 1, 0)

Modified Z-Score =
-- More robust to skewed data / pre-existing extreme values than the
-- standard Z-score, since it uses median + median absolute deviation (MAD)
-- rather than mean + standard deviation.
VAR CurrentValue = Monitoring[Value]
VAR CurrentNutrient = Monitoring[NutrientName]
VAR NutrientRows =
    FILTER(Monitoring, Monitoring[NutrientName] = CurrentNutrient && NOT ISBLANK(Monitoring[Value]))
VAR MedianValue = MEDIANX(NutrientRows, Monitoring[Value])
VAR MAD =
    MEDIANX(
        ADDCOLUMNS(NutrientRows, "AbsDev", ABS(Monitoring[Value] - MedianValue)),
        [AbsDev]
    )
RETURN
    SWITCH(
        TRUE(),
        ISBLANK(CurrentValue), BLANK(),
        MAD = 0, 0,
        0.6745 * (CurrentValue - MedianValue) / MAD
    )

Is Outlier (Modified Z) = IF(ABS([Modified Z-Score]) > 3.5, 1, 0)
```

## 4. Time intelligence — rolling average & month-over-month change

```dax
Rolling Avg (3 Mo) =
CALCULATE(
    [Avg Value],
    DATESINPERIOD(DateTable[Date], MAX(DateTable[Date]), -3, MONTH)
)

MoM Change % =
VAR CurrentAvg = [Avg Value]
VAR PreviousAvg = CALCULATE([Avg Value], PREVIOUSMONTH(DateTable[Date]))
RETURN
    DIVIDE(CurrentAvg - PreviousAvg, PreviousAvg, BLANK()) * 100
```

## 5. Linear regression for trend lines (slope, intercept, R²)

```dax
Regression Slope =
VAR XBar = AVERAGE(Monitoring[DateNum])
VAR YBar = AVERAGE(Monitoring[Value])
VAR Numerator = SUMX(Monitoring, (Monitoring[DateNum] - XBar) * (Monitoring[Value] - YBar))
VAR Denominator = SUMX(Monitoring, (Monitoring[DateNum] - XBar) ^ 2)
RETURN
    DIVIDE(Numerator, Denominator)

Regression Intercept =
VAR Slope = [Regression Slope]
VAR XBar = AVERAGE(Monitoring[DateNum])
VAR YBar = AVERAGE(Monitoring[Value])
RETURN
    YBar - Slope * XBar

Regression R2 =
VAR Slope = [Regression Slope]
VAR Intercept = [Regression Intercept]
VAR YMean = AVERAGE(Monitoring[Value])
VAR SS_Total = SUMX(Monitoring, (Monitoring[Value] - YMean) ^ 2)
VAR SS_Residual =
    SUMX(Monitoring, (Monitoring[Value] - (Slope * Monitoring[DateNum] + Intercept)) ^ 2)
RETURN
    DIVIDE(SS_Total - SS_Residual, SS_Total)
```

## 6. Volatility classification

```dax
Volatility Score = DIVIDE([Std Dev (Cleaned)], [Avg Value])

Volatility Category =
SWITCH(
    TRUE(),
    [Volatility Score] < 0.05, "Stable",
    [Volatility Score] < 0.15, "Moderate",
    [Volatility Score] < 0.30, "Volatile",
    "Highly Volatile"
)
```

---

## Power Query (M) — unit conversion pattern

Simplified pattern for dynamically converting reported values into a common
unit before any comparison happens:

```m
let
    Source = MonitoringRaw,
    MergedWithConversionTable =
        Table.NestedJoin(
            Source, {"UnitOfMeasure"},
            UOMConversionTable, {"FromUnit"},
            "ConversionInfo", JoinKind.LeftOuter
        ),
    ExpandedConversion =
        Table.ExpandTableColumn(
            MergedWithConversionTable, "ConversionInfo", {"ConversionFactor", "ToUnit"}
        ),
    AddedConvertedValue =
        Table.AddColumn(
            ExpandedConversion, "ConvertedValue",
            each [Value] * [ConversionFactor], type number
        )
in
    AddedConvertedValue
```

## Power Query (M) — nutrient name harmonization pattern

```m
let
    Source = MonitoringRaw,
    MergedWithNameMap =
        Table.NestedJoin(
            Source, {"LabDescription"},
            NameConversionTable, {"LabDescription"},
            "NameMap", JoinKind.LeftOuter
        ),
    ExpandedNameMap =
        Table.ExpandTableColumn(MergedWithNameMap, "NameMap", {"CommonName"})
in
    ExpandedNameMap
```
