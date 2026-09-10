"""Thin skfolio helpers for research notebooks.

Users compose any skfolio/sklearn estimator before fit. Orion only prepares
returns (overlap + drop zero-variance) and wraps labeled weights. Annualization
defaults to 365. Not a sklearn Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pandas as pd
from skfolio import RiskMeasure
from skfolio.optimization import MeanRisk, ObjectiveFunction

from orion_finance_sdk_py.stats.constants import DEFAULT_PERIODS_PER_YEAR, ZERO_VARIANCE
from orion_finance_sdk_py.stats.rfr import daily_rfr
from orion_finance_sdk_py.stats.series import ReturnSeries


@runtime_checkable
class PortfolioEstimator(Protocol):
    """Minimal skfolio/sklearn surface used by Orion (weights_ appear after fit)."""

    def fit(self, X: pd.DataFrame, y: object = None, **kwargs: object) -> object:
        """Fit the estimator to the provided data."""
        ...

    def predict(self, X: pd.DataFrame) -> object:
        """Predict using the fitted estimator on the provided data."""
        ...


@dataclass
class FittedPortfolio:
    """Labeled portfolio weights plus the fitted estimator."""

    weights: pd.Series
    model: PortfolioEstimator
    dropped: tuple[str, ...]

    def predict(self, returns: pd.DataFrame) -> object:
        """Predict an out-of-sample portfolio on the kept columns."""
        kept = [name for name in self.weights.index if name in returns.columns]
        return self.model.predict(returns.loc[:, kept])


def _as_frame(returns: ReturnSeries | pd.DataFrame) -> pd.DataFrame:
    """Contiguous daily returns as a DataFrame."""
    return returns.returns if isinstance(returns, ReturnSeries) else returns


def chronological_split(
    returns: ReturnSeries | pd.DataFrame,
    test_size: float = 0.33,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Time-ordered train/test split (no shuffle) on overlapping rows."""
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be in (0, 1)")
    overlap = _as_frame(returns).dropna(how="any")
    n = len(overlap)
    n_test = int(round(n * test_size))
    n_train = n - n_test
    if n_train < 1 or n_test < 1:
        raise ValueError("split would leave an empty train or test set")
    return overlap.iloc[:n_train], overlap.iloc[n_train:]


def drop_zero_variance(
    returns: pd.DataFrame,
    *,
    threshold: float = ZERO_VARIANCE,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Drop columns whose population std is at or below ``threshold``."""
    vol = returns.std(ddof=0)
    dropped = tuple(str(name) for name in vol.index[vol <= threshold])
    if dropped:
        returns = returns.drop(columns=list(dropped))
    return returns, dropped


def prepare_returns(
    returns: ReturnSeries | pd.DataFrame,
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Overlap complete rows and drop flat assets before fitting."""
    overlap = _as_frame(returns).dropna(how="any")
    return drop_zero_variance(overlap)


def fit_estimator(
    returns: ReturnSeries | pd.DataFrame,
    model: PortfolioEstimator,
) -> FittedPortfolio:
    """Prepare returns, fit ``model``, and return labeled weights."""
    frame, dropped = prepare_returns(returns)
    if frame.shape[1] < 2 or frame.shape[0] < 2:
        raise ValueError("Estimator needs at least 2 assets and 2 observations")
    model.fit(frame)
    weights_raw = getattr(model, "weights_", None)
    if weights_raw is None:
        raise ValueError("Estimator must expose weights_ after fit")
    weights = pd.Series(weights_raw, index=frame.columns, dtype=float)
    return FittedPortfolio(weights=weights, model=model, dropped=dropped)


def min_variance_model(
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> MeanRisk:
    """Unfitted long-only minimum-variance ``MeanRisk`` with Orion defaults."""
    rf_period = daily_rfr(rfr, periods_per_year=periods_per_year)
    return MeanRisk(
        risk_free_rate=rf_period,
        portfolio_params={"annualized_factor": float(periods_per_year)},
    )


def max_sortino_model(
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> MeanRisk:
    """Unfitted max-Sortino ``MeanRisk`` with Orion defaults."""
    rf_period = daily_rfr(rfr, periods_per_year=periods_per_year)
    return MeanRisk(
        objective_function=ObjectiveFunction.MAXIMIZE_RATIO,
        risk_measure=RiskMeasure.SEMI_VARIANCE,
        risk_free_rate=rf_period,
        portfolio_params={"annualized_factor": float(periods_per_year)},
    )


def max_sharpe_model(
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> MeanRisk:
    """Unfitted max-Sharpe ``MeanRisk`` with Orion defaults."""
    rf_period = daily_rfr(rfr, periods_per_year=periods_per_year)
    return MeanRisk(
        objective_function=ObjectiveFunction.MAXIMIZE_RATIO,
        risk_measure=RiskMeasure.VARIANCE,
        risk_free_rate=rf_period,
        portfolio_params={"annualized_factor": float(periods_per_year)},
    )


def min_variance(
    returns: ReturnSeries | pd.DataFrame,
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> FittedPortfolio:
    """Minimum-variance long-only portfolio (skfolio ``MeanRisk`` default)."""
    return fit_estimator(
        returns, min_variance_model(rfr=rfr, periods_per_year=periods_per_year)
    )


def max_sortino(
    returns: ReturnSeries | pd.DataFrame,
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> FittedPortfolio:
    """Maximize Sortino ratio (mean / semi-deviation)."""
    return fit_estimator(
        returns, max_sortino_model(rfr=rfr, periods_per_year=periods_per_year)
    )


def max_sharpe(
    returns: ReturnSeries | pd.DataFrame,
    *,
    rfr: float = 0.0,
    periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
) -> FittedPortfolio:
    """Maximize Sharpe ratio (mean excess return / standard deviation)."""
    return fit_estimator(
        returns, max_sharpe_model(rfr=rfr, periods_per_year=periods_per_year)
    )
