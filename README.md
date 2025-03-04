# MACARON-PlanComplexity
This projects stems from MACARON and focuses on (RT) Plan Complexity Metrics
It computes different plan complexity metrics, either custom or taken from external libraries. 

## Output
For each RTplan, it provides a folder containing CSV files and PNG images (plots)

## Custom Metrics

The tool computes the following custom metrics, which are printed in a CSV

per Beam:
- MUbeam
- MUfinalweight
- M
- MCS
- MCSV
- MFC
- BI
- avgApertureLessThan1cm
- yDiffLessThan1cm
- SAS2
- SAS5
- SAS10
- SAS20

per Plan:
- MUplan
- Mplan
- MCSplan
- MCSVplan
- MFCplan
- PI
- nCP
- avgApertureLessThan1cm
- yDiffLessThan1cm

## Metrics from Existing Frameworks

Moreover, it plots the following graphs, and the corresponding CSV file:
- ApertureIrregularityMetric
- AreaMetricEstimator
- MeanAreaMetricEstimator
- PyComplexityMetric
using the library at "https://github.com/victorgabr/ApertureComplexity", from
Victor Gabriel Leandro Alves, D.Sc.
University of Michigan, Radiation Oncology https://github.com/umro/Complexity

## Dependencies of the Python
- numpy
- matplotlib
- pydicom
- shutil
- and the GitHub library above

## Contributors
- Margherita Zani, Silvia Calusi (AUO Careggi, Careggi Hospital, Florence, Italy)
- Tommaso Zoppi (University of Florence)
