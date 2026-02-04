"""Statistical Analysis Tool

Provides comprehensive statistical operations for data exploration and analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class StatisticalSummary:
    """Container for statistical analysis results"""

    metric: str
    value: float | str | dict
    description: str | None = None
    metadata: dict | None = field(default_factory=dict)


class StatisticsAnalyzer:
    """Statistical analysis tool for data exploration"""

    def __init__(self):
        """Initialize the statistics analyzer"""
        pass

    async def describe_dataframe(
        self, data: pd.DataFrame, include_percentiles: bool = True
    ) -> dict:
        """
        Generate comprehensive descriptive statistics for a DataFrame

        Args:
            data: Input DataFrame
            include_percentiles: Include quartiles and percentiles

        Returns:
            Dictionary with shape, columns, dtypes, summary stats, missing values
        """
        result = {
            "shape": data.shape,
            "columns": data.columns.tolist(),
            "dtypes": data.dtypes.astype(str).to_dict(),
            "memory_usage": data.memory_usage(deep=True).to_dict(),
        }

        # Missing values
        missing = data.isnull().sum()
        result["missing_values"] = missing[missing > 0].to_dict()
        result["missing_percentage"] = (missing[missing > 0] / len(data) * 100).to_dict()

        # Summary statistics for numeric columns
        if include_percentiles:
            numeric_summary = data.describe().to_dict()
            result["summary_statistics"] = numeric_summary

        return result

    async def calculate_statistics(
        self,
        series: pd.Series | list,
        metrics: list[str] | None = None,
    ) -> list[StatisticalSummary]:
        """
        Calculate specified statistical metrics for a series

        Args:
            series: Input data (Series or list)
            metrics: List of metrics to calculate (if None, calculate all)

        Returns:
            List of StatisticalSummary objects
        """
        if isinstance(series, list):
            series = pd.Series(series)

        # Remove NaN values
        clean_series = series.dropna()

        if len(clean_series) == 0:
            return [
                StatisticalSummary(
                    metric="error", value="No valid data", description="All values are NaN"
                )
            ]

        # Default to all metrics if none specified
        if metrics is None:
            metrics = ["mean", "median", "mode", "std", "var", "min", "max", "quartiles"]

        results = []

        if "mean" in metrics:
            results.append(
                StatisticalSummary(
                    metric="mean", value=float(clean_series.mean()), description="Arithmetic mean"
                )
            )

        if "median" in metrics:
            results.append(
                StatisticalSummary(
                    metric="median",
                    value=float(clean_series.median()),
                    description="Middle value",
                )
            )

        if "mode" in metrics:
            mode_result = clean_series.mode()
            mode_value = mode_result.iloc[0] if len(mode_result) > 0 else None
            results.append(
                StatisticalSummary(
                    metric="mode",
                    value=float(mode_value) if mode_value is not None else "N/A",
                    description="Most frequent value",
                )
            )

        if "std" in metrics:
            results.append(
                StatisticalSummary(
                    metric="std",
                    value=float(clean_series.std()),
                    description="Standard deviation",
                )
            )

        if "var" in metrics:
            results.append(
                StatisticalSummary(
                    metric="var", value=float(clean_series.var()), description="Variance"
                )
            )

        if "min" in metrics:
            results.append(
                StatisticalSummary(
                    metric="min", value=float(clean_series.min()), description="Minimum value"
                )
            )

        if "max" in metrics:
            results.append(
                StatisticalSummary(
                    metric="max", value=float(clean_series.max()), description="Maximum value"
                )
            )

        if "quartiles" in metrics:
            q1 = clean_series.quantile(0.25)
            q2 = clean_series.quantile(0.50)
            q3 = clean_series.quantile(0.75)
            results.append(
                StatisticalSummary(
                    metric="quartiles",
                    value={"Q1": float(q1), "Q2": float(q2), "Q3": float(q3)},
                    description="25th, 50th, 75th percentiles",
                )
            )

        if "skew" in metrics:
            results.append(
                StatisticalSummary(
                    metric="skew",
                    value=float(clean_series.skew()),
                    description="Measure of asymmetry",
                )
            )

        if "kurtosis" in metrics:
            results.append(
                StatisticalSummary(
                    metric="kurtosis",
                    value=float(clean_series.kurtosis()),
                    description="Measure of tail heaviness",
                )
            )

        return results

    async def correlation_matrix(
        self,
        data: pd.DataFrame,
        method: Literal["pearson", "spearman", "kendall"] = "pearson",
    ) -> dict:
        """
        Calculate correlation matrix and identify strong correlations

        Args:
            data: Input DataFrame (only numeric columns will be used)
            method: Correlation method

        Returns:
            Dictionary with correlation matrix and strong correlations
        """
        # Select only numeric columns
        numeric_data = data.select_dtypes(include=[np.number])

        if numeric_data.shape[1] < 2:
            return {
                "matrix": {},
                "strong_correlations": [],
                "error": "Need at least 2 numeric columns",
            }

        # Calculate correlation matrix
        corr_matrix = numeric_data.corr(method=method)

        # Identify strong correlations (|r| > 0.7)
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]

                if abs(corr_value) > 0.7:
                    strong_correlations.append(
                        {"column1": col1, "column2": col2, "correlation": float(corr_value)}
                    )

        return {
            "matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "method": method,
        }

    async def linear_regression(self, x: pd.Series, y: pd.Series) -> dict:
        """
        Perform simple linear regression

        Args:
            x: Independent variable
            y: Dependent variable

        Returns:
            Dictionary with regression parameters
        """
        # Remove NaN values
        valid_idx = ~(x.isna() | y.isna())
        x_clean = x[valid_idx]
        y_clean = y[valid_idx]

        if len(x_clean) < 2:
            return {"error": "Need at least 2 valid data points"}

        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)

        return {
            "slope": float(slope),
            "intercept": float(intercept),
            "r_value": float(r_value),
            "r_squared": float(r_value**2),
            "p_value": float(p_value),
            "std_err": float(std_err),
            "equation": f"y = {slope:.4f}x + {intercept:.4f}",
        }

    async def t_test(
        self,
        sample1: pd.Series | list,
        sample2: pd.Series | list | None = None,
        alternative: Literal["two-sided", "less", "greater"] = "two-sided",
    ) -> dict:
        """
        Perform t-test (one-sample or two-sample)

        Args:
            sample1: First sample
            sample2: Second sample (None for one-sample test against population mean of 0)
            alternative: Alternative hypothesis

        Returns:
            Dictionary with test statistic, p-value, and interpretation
        """
        if isinstance(sample1, list):
            sample1 = pd.Series(sample1)

        sample1_clean = sample1.dropna()

        if sample2 is None:
            # One-sample t-test
            statistic, p_value = stats.ttest_1samp(sample1_clean, 0, alternative=alternative)
            test_type = "one-sample"
        else:
            # Two-sample t-test
            if isinstance(sample2, list):
                sample2 = pd.Series(sample2)
            sample2_clean = sample2.dropna()
            statistic, p_value = stats.ttest_ind(
                sample1_clean, sample2_clean, alternative=alternative
            )
            test_type = "two-sample"

        # Interpretation
        is_significant = p_value < 0.05

        return {
            "test_type": test_type,
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alternative": alternative,
            "is_significant": is_significant,
            "interpretation": (
                "Reject null hypothesis (significant difference)"
                if is_significant
                else "Fail to reject null hypothesis (no significant difference)"
            ),
        }

    async def chi_square_test(
        self, observed: pd.Series | list, expected: pd.Series | list | None = None
    ) -> dict:
        """
        Perform chi-square goodness of fit test

        Args:
            observed: Observed frequencies
            expected: Expected frequencies (if None, assumes uniform distribution)

        Returns:
            Dictionary with test statistic, p-value, and interpretation
        """
        if isinstance(observed, pd.Series):
            observed = observed.values
        if expected is not None and isinstance(expected, pd.Series):
            expected = expected.values

        if expected is None:
            # Assume uniform distribution
            expected = np.full(len(observed), np.mean(observed))

        statistic, p_value = stats.chisquare(observed, expected)

        is_significant = p_value < 0.05

        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "degrees_of_freedom": len(observed) - 1,
            "is_significant": is_significant,
            "interpretation": (
                "Reject null hypothesis (data does not fit expected distribution)"
                if is_significant
                else "Fail to reject null hypothesis (data fits expected distribution)"
            ),
        }

    async def test_normality(
        self, data: pd.Series | list, method: Literal["shapiro", "kstest"] = "shapiro"
    ) -> dict:
        """
        Test if data follows a normal distribution

        Args:
            data: Input data
            method: Test method (shapiro or kstest)

        Returns:
            Dictionary with p-value and normality determination
        """
        if isinstance(data, list):
            data = pd.Series(data)

        data_clean = data.dropna()

        if len(data_clean) < 3:
            return {"error": "Need at least 3 data points"}

        if method == "shapiro":
            statistic, p_value = stats.shapiro(data_clean)
        else:  # kstest
            statistic, p_value = stats.kstest(data_clean, "norm")

        is_normal = p_value > 0.05

        return {
            "method": method,
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_normal": is_normal,
            "interpretation": (
                "Data appears to be normally distributed"
                if is_normal
                else "Data does not appear to be normally distributed"
            ),
        }

    async def identify_outliers(
        self,
        data: pd.Series | list,
        method: Literal["iqr", "zscore"] = "iqr",
        threshold: float | None = None,
    ) -> dict:
        """
        Identify outliers in the data

        Args:
            data: Input data
            method: Detection method (iqr or zscore)
            threshold: Custom threshold (1.5 for IQR, 3.0 for z-score by default)

        Returns:
            Dictionary with outlier indices, values, and statistics
        """
        if isinstance(data, list):
            data = pd.Series(data)

        data_clean = data.dropna()

        if method == "iqr":
            # Interquartile Range method
            if threshold is None:
                threshold = 1.5

            Q1 = data_clean.quantile(0.25)
            Q3 = data_clean.quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR

            outlier_mask = (data_clean < lower_bound) | (data_clean > upper_bound)

        else:  # zscore
            # Z-score method
            if threshold is None:
                threshold = 3.0

            z_scores = np.abs(stats.zscore(data_clean))
            outlier_mask = z_scores > threshold
            lower_bound = data_clean.mean() - threshold * data_clean.std()
            upper_bound = data_clean.mean() + threshold * data_clean.std()

        outlier_indices = data_clean[outlier_mask].index.tolist()
        outlier_values = data_clean[outlier_mask].tolist()

        return {
            "method": method,
            "threshold": threshold,
            "outlier_indices": outlier_indices,
            "outlier_values": outlier_values,
            "count": len(outlier_indices),
            "percentage": float(len(outlier_indices) / len(data_clean) * 100),
            "bounds": {"lower": float(lower_bound), "upper": float(upper_bound)},
        }

    async def filter_data(self, data: pd.DataFrame, conditions: dict[str, dict]) -> pd.DataFrame:
        """
        Filter DataFrame based on conditions

        Args:
            data: Input DataFrame
            conditions: Dictionary of column conditions
                Example: {"age": {">": 18, "<": 65}, "status": {"==": "active"}}

        Returns:
            Filtered DataFrame
        """
        filtered_data = data.copy()

        for column, condition_dict in conditions.items():
            if column not in data.columns:
                continue

            for operator, value in condition_dict.items():
                if operator == ">":
                    filtered_data = filtered_data[filtered_data[column] > value]
                elif operator == "<":
                    filtered_data = filtered_data[filtered_data[column] < value]
                elif operator == ">=":
                    filtered_data = filtered_data[filtered_data[column] >= value]
                elif operator == "<=":
                    filtered_data = filtered_data[filtered_data[column] <= value]
                elif operator == "==":
                    filtered_data = filtered_data[filtered_data[column] == value]
                elif operator == "!=":
                    filtered_data = filtered_data[filtered_data[column] != value]

        return filtered_data

    async def group_and_aggregate(
        self,
        data: pd.DataFrame,
        group_by: str | list[str],
        aggregations: dict[str, str | list[str]],
    ) -> pd.DataFrame:
        """
        Group data and apply aggregation functions

        Args:
            data: Input DataFrame
            group_by: Column(s) to group by
            aggregations: Dictionary of column: function(s) pairs
                Example: {"sales": ["sum", "mean"], "quantity": "count"}

        Returns:
            Grouped and aggregated DataFrame
        """
        return data.groupby(group_by).agg(aggregations)

    async def pivot_table(
        self,
        data: pd.DataFrame,
        index: str | list[str],
        columns: str,
        values: str,
        aggfunc: str = "mean",
    ) -> pd.DataFrame:
        """
        Create a pivot table

        Args:
            data: Input DataFrame
            index: Column(s) to use as row index
            columns: Column to use as column headers
            values: Column to aggregate
            aggfunc: Aggregation function

        Returns:
            Pivot table DataFrame
        """
        return pd.pivot_table(data, index=index, columns=columns, values=values, aggfunc=aggfunc)

    async def load_from_dict(self, data: dict | list[dict]) -> pd.DataFrame:
        """
        Create DataFrame from dictionary or list of dictionaries

        Args:
            data: Input data

        Returns:
            DataFrame
        """
        return pd.DataFrame(data)

    async def convert_to_numeric(
        self, data: pd.DataFrame, columns: list[str] | None = None, errors: str = "coerce"
    ) -> pd.DataFrame:
        """
        Convert columns to numeric type

        Args:
            data: Input DataFrame
            columns: Columns to convert (if None, convert all possible columns)
            errors: How to handle errors ('raise', 'coerce', 'ignore')

        Returns:
            DataFrame with converted columns
        """
        result = data.copy()

        if columns is None:
            columns = data.columns.tolist()

        for col in columns:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors=errors)

        return result

    async def handle_missing_values(
        self,
        data: pd.DataFrame,
        strategy: Literal["drop", "mean", "median", "mode", "forward_fill", "backward_fill"],
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Handle missing values using specified strategy

        Args:
            data: Input DataFrame
            strategy: Strategy for handling missing values
            columns: Columns to apply strategy to (if None, apply to all)

        Returns:
            DataFrame with handled missing values
        """
        result = data.copy()

        if columns is None:
            columns = data.columns.tolist()

        if strategy == "drop":
            result = result.dropna(subset=columns)
        elif strategy == "mean":
            for col in columns:
                if col in result.columns and pd.api.types.is_numeric_dtype(result[col]):
                    result[col] = result[col].fillna(result[col].mean())
        elif strategy == "median":
            for col in columns:
                if col in result.columns and pd.api.types.is_numeric_dtype(result[col]):
                    result[col] = result[col].fillna(result[col].median())
        elif strategy == "mode":
            for col in columns:
                if col in result.columns:
                    mode_value = result[col].mode()
                    if len(mode_value) > 0:
                        result[col] = result[col].fillna(mode_value[0])
        elif strategy == "forward_fill":
            result[columns] = result[columns].ffill()
        elif strategy == "backward_fill":
            result[columns] = result[columns].bfill()

        return result
