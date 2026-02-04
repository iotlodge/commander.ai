"""Data Visualization Tool

Provides seaborn-based charting capabilities for data exploration.
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from backend.core.config import get_settings

# Use non-interactive backend for server environments
matplotlib.use("Agg")


@dataclass
class ChartResult:
    """Container for chart generation results"""

    chart_type: str
    file_path: str | None
    base64_image: str | None
    width: int
    height: int
    metadata: dict = field(default_factory=dict)


class ChartGenerator:
    """Seaborn-based data visualization tool"""

    def __init__(self, output_dir: str | None = None):
        """
        Initialize the chart generator

        Args:
            output_dir: Directory to save charts (defaults to settings.chart_output_dir)
        """
        settings = get_settings()
        self.output_dir = Path(output_dir or settings.chart_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set seaborn style
        sns.set_theme(style=settings.chart_style)
        sns.set_palette(settings.chart_palette)

        self.settings = settings

    async def scatter_plot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        hue: str | None = None,
        size: str | None = None,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a scatter plot

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            hue: Column for color grouping
            size: Column for point size
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments passed to sns.scatterplot

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.scatterplot(data=data, x=x, y=y, hue=hue, size=size, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or f"{x} vs {y}", x, y)

        result = await self._finalize_chart(fig, "scatter_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def line_plot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str | list[str],
        hue: str | None = None,
        markers: bool = False,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a line plot

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column(s) for y-axis
            hue: Column for color grouping
            markers: Show markers on data points
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        if isinstance(y, list):
            for col in y:
                ax.plot(data[x], data[col], marker="o" if markers else None, label=col)
            ax.legend()
            y_label = "Value"
        else:
            sns.lineplot(
                data=data,
                x=x,
                y=y,
                hue=hue,
                markers=markers,
                dashes=False,
                ax=ax,
                **kwargs,
            )
            y_label = y

        self._apply_common_styling(ax, title or "Line Plot", x, y_label)

        result = await self._finalize_chart(fig, "line_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def bar_chart(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        hue: str | None = None,
        orientation: Literal["v", "h"] = "v",
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a bar chart

        Args:
            data: Input DataFrame
            x: Column for x-axis (or y-axis if orientation='h')
            y: Column for y-axis (or x-axis if orientation='h')
            hue: Column for color grouping
            orientation: 'v' for vertical, 'h' for horizontal
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        if orientation == "h":
            sns.barplot(data=data, y=x, x=y, hue=hue, orient="h", ax=ax, **kwargs)
        else:
            sns.barplot(data=data, x=x, y=y, hue=hue, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or "Bar Chart", x, y)

        result = await self._finalize_chart(fig, "bar_chart", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def histogram(
        self,
        data: pd.DataFrame,
        column: str,
        bins: int | str = "auto",
        kde: bool = False,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a histogram

        Args:
            data: Input DataFrame
            column: Column to plot
            bins: Number of bins or binning strategy
            kde: Show kernel density estimate
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.histplot(data=data, x=column, bins=bins, kde=kde, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or f"Distribution of {column}", column, "Frequency")

        result = await self._finalize_chart(fig, "histogram", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def box_plot(
        self,
        data: pd.DataFrame,
        x: str | None = None,
        y: str | None = None,
        hue: str | None = None,
        orientation: Literal["v", "h"] = "v",
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a box plot

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            hue: Column for color grouping
            orientation: 'v' for vertical, 'h' for horizontal
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        if orientation == "h":
            sns.boxplot(data=data, y=x, x=y, hue=hue, orient="h", ax=ax, **kwargs)
        else:
            sns.boxplot(data=data, x=x, y=y, hue=hue, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or "Box Plot", x or "", y or "")

        result = await self._finalize_chart(fig, "box_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def violin_plot(
        self,
        data: pd.DataFrame,
        x: str | None = None,
        y: str | None = None,
        hue: str | None = None,
        split: bool = False,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a violin plot

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            hue: Column for color grouping
            split: Split violins for hue variable
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.violinplot(data=data, x=x, y=y, hue=hue, split=split, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or "Violin Plot", x or "", y or "")

        result = await self._finalize_chart(fig, "violin_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def heatmap(
        self,
        data: pd.DataFrame,
        annot: bool = True,
        fmt: str = ".2f",
        cmap: str = "coolwarm",
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a heatmap

        Args:
            data: Input DataFrame (typically a correlation matrix)
            annot: Annotate cells with values
            fmt: String format for annotations
            cmap: Color map
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.heatmap(data, annot=annot, fmt=fmt, cmap=cmap, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or "Heatmap", "", "")

        result = await self._finalize_chart(fig, "heatmap", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def pair_plot(
        self,
        data: pd.DataFrame,
        columns: list[str] | None = None,
        hue: str | None = None,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a pair plot (pairwise relationships)

        Args:
            data: Input DataFrame
            columns: Columns to include (if None, use all numeric columns)
            hue: Column for color grouping
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        if columns:
            plot_data = data[columns + ([hue] if hue else [])]
        else:
            plot_data = data

        pairplot = sns.pairplot(plot_data, hue=hue, **kwargs)

        if title:
            pairplot.fig.suptitle(title, y=1.02)

        result = await self._finalize_chart(pairplot.fig, "pair_plot", save, return_base64)
        self._cleanup_figure(pairplot.fig)

        return result

    async def count_plot(
        self,
        data: pd.DataFrame,
        x: str | None = None,
        y: str | None = None,
        hue: str | None = None,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a count plot (categorical counts)

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            hue: Column for color grouping
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.countplot(data=data, x=x, y=y, hue=hue, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or "Count Plot", x or "", y or "Count")

        result = await self._finalize_chart(fig, "count_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    async def regression_plot(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        order: int = 1,
        ci: int = 95,
        title: str | None = None,
        save: bool = True,
        return_base64: bool = False,
        **kwargs,
    ) -> ChartResult:
        """
        Create a regression plot with confidence interval

        Args:
            data: Input DataFrame
            x: Column for x-axis
            y: Column for y-axis
            order: Polynomial order
            ci: Confidence interval size
            title: Chart title
            save: Save to file
            return_base64: Return base64 encoded image
            **kwargs: Additional arguments

        Returns:
            ChartResult with file path and/or base64 image
        """
        fig, ax = plt.subplots(
            figsize=(self.settings.chart_default_width, self.settings.chart_default_height)
        )

        sns.regplot(data=data, x=x, y=y, order=order, ci=ci, ax=ax, **kwargs)

        self._apply_common_styling(ax, title or f"Regression: {x} vs {y}", x, y)

        result = await self._finalize_chart(fig, "regression_plot", save, return_base64)
        self._cleanup_figure(fig)

        return result

    def _generate_filename(self, chart_type: str) -> str:
        """Generate unique filename for chart"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{chart_type}_{timestamp}.{self.settings.chart_format}"

    def _save_figure(self, fig: plt.Figure, filename: str) -> str:
        """Save figure to file and return absolute path"""
        file_path = self.output_dir / filename
        fig.savefig(
            file_path, dpi=self.settings.chart_dpi, bbox_inches="tight", format=self.settings.chart_format
        )
        return str(file_path.absolute())

    def _figure_to_base64(self, fig: plt.Figure) -> str:
        """Convert figure to base64 encoded string (without prefix)"""
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=self.settings.chart_dpi, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()
        return image_base64

    def _apply_common_styling(
        self, ax: plt.Axes, title: str | None, xlabel: str, ylabel: str
    ) -> None:
        """Apply common styling to chart"""
        if title:
            ax.set_title(title, fontsize=14, fontweight="bold")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=11)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=11)
        ax.grid(alpha=0.3)

    def _cleanup_figure(self, fig: plt.Figure) -> None:
        """Close figure to free memory"""
        plt.close(fig)

    async def _finalize_chart(
        self, fig: plt.Figure, chart_type: str, save: bool, return_base64: bool
    ) -> ChartResult:
        """Finalize chart by saving and/or converting to base64"""
        file_path = None
        base64_image = None

        if save:
            filename = self._generate_filename(chart_type)
            file_path = self._save_figure(fig, filename)

        if return_base64:
            base64_image = self._figure_to_base64(fig)

        # Get figure dimensions
        width, height = fig.get_size_inches()

        return ChartResult(
            chart_type=chart_type,
            file_path=file_path,
            base64_image=base64_image,
            width=int(width),
            height=int(height),
            metadata={"dpi": self.settings.chart_dpi, "format": self.settings.chart_format},
        )

    def set_style(self, style: str) -> None:
        """
        Change seaborn style

        Args:
            style: Style name (darkgrid, whitegrid, dark, white, ticks)
        """
        sns.set_theme(style=style)

    def set_palette(self, palette: str) -> None:
        """
        Change color palette

        Args:
            palette: Palette name
        """
        sns.set_palette(palette)

    def list_saved_charts(self) -> list[dict]:
        """
        List all saved charts in the output directory

        Returns:
            List of chart information dictionaries
        """
        charts = []
        for file_path in self.output_dir.glob(f"*.{self.settings.chart_format}"):
            charts.append(
                {
                    "name": file_path.name,
                    "path": str(file_path.absolute()),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                }
            )
        return sorted(charts, key=lambda x: x["modified"], reverse=True)

    async def cleanup_old_charts(self, older_than_days: int = 7) -> dict:
        """
        Delete charts older than specified days

        Args:
            older_than_days: Delete files older than this many days

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0
        deleted_size = 0

        for file_path in self.output_dir.glob(f"*.{self.settings.chart_format}"):
            file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

            if file_modified < cutoff_date:
                deleted_size += file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1

        return {
            "deleted_count": deleted_count,
            "deleted_size_bytes": deleted_size,
            "cutoff_date": cutoff_date.isoformat(),
        }
