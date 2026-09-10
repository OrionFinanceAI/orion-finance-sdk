"""Tests for IntentSession and weights_to_intent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from orion_finance_sdk_py.lifecycle import IntentSession, weights_to_intent
from orion_finance_sdk_py.stats.portfolio import (
    fit_estimator,
    max_sharpe,
    max_sharpe_model,
    prepare_returns,
)
from orion_finance_sdk_py.stats.series import ReturnSeries
from orion_finance_sdk_py.utils import checksum_address

ADDR_A = "0x1111111111111111111111111111111111111111"
ADDR_B = "0x2222222222222222222222222222222222222222"


class _FakeEstimator:
    """Minimal non-MeanRisk estimator for IntentSession."""

    def __init__(self) -> None:
        self.weights_ = None
        self._columns: list[str] = []

    def fit(self, X: pd.DataFrame, y=None, **kwargs):
        self._columns = [str(c) for c in X.columns]
        n = len(self._columns)
        self.weights_ = np.full(n, 1.0 / n)
        return self

    def predict(self, X: pd.DataFrame):
        return ("predicted", tuple(X.columns))


def _daily_index(n: int) -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")


def test_prepare_returns_drops_flat_assets() -> None:
    idx = _daily_index(10)
    frame = pd.DataFrame(
        {
            "risky": np.linspace(0.01, 0.02, 10),
            "flat": np.zeros(10),
            "other": np.linspace(-0.01, 0.01, 10),
        },
        index=idx,
    )
    prepared, dropped = prepare_returns(frame)
    assert "flat" in dropped
    assert list(prepared.columns) == ["risky", "other"]


def test_weights_to_intent_maps_labels_and_renormalizes() -> None:
    weights = pd.Series({"USDC": 0.5, "WETH": 0.4, "dust": 1e-15})
    mapping = {"USDC": ADDR_A, "WETH": ADDR_B, "dust": ADDR_A}
    intent = weights_to_intent(weights, address_by_label=mapping)
    assert set(intent) == {checksum_address(ADDR_A), checksum_address(ADDR_B)}
    assert sum(intent.values()) == pytest.approx(1.0)
    assert intent[checksum_address(ADDR_A)] == pytest.approx(0.5 / 0.9)
    assert intent[checksum_address(ADDR_B)] == pytest.approx(0.4 / 0.9)


def test_weights_to_intent_accepts_address_labels() -> None:
    weights = pd.Series({ADDR_A: 0.25, ADDR_B: 0.75})
    intent = weights_to_intent(weights)
    assert intent[checksum_address(ADDR_A)] == pytest.approx(0.25)
    assert intent[checksum_address(ADDR_B)] == pytest.approx(0.75)


def test_max_sharpe_model_is_unfitted_until_fit_estimator() -> None:
    model = max_sharpe_model(rfr=0.041)
    assert not hasattr(model, "weights_")
    rng = np.random.default_rng(1)
    idx = _daily_index(40)
    rs = ReturnSeries.from_returns(
        pd.DataFrame(
            {
                "a": 0.001 + 0.01 * rng.normal(size=40),
                "b": 0.002 + 0.012 * rng.normal(size=40),
            },
            index=idx,
        )
    )
    oneshot = max_sharpe(rs, rfr=0.041)
    via_factory = fit_estimator(rs, max_sharpe_model(rfr=0.041))
    assert oneshot.weights.sum() == pytest.approx(1.0)
    assert via_factory.weights.sum() == pytest.approx(1.0)
    assert hasattr(via_factory.model, "weights_")


def test_intent_session_requires_fit_before_predict() -> None:
    session = IntentSession(_FakeEstimator())
    with pytest.raises(ValueError, match="not been fit"):
        session.predict(pd.DataFrame({"a": [0.01]}))


def test_intent_session_fit_predict_with_fake_estimator() -> None:
    idx = _daily_index(20)
    frame = pd.DataFrame(
        {
            "alpha": np.linspace(0.01, 0.02, 20),
            "beta": np.linspace(-0.01, 0.01, 20),
        },
        index=idx,
    )
    session = IntentSession(
        _FakeEstimator(),
        address_by_label={"alpha": ADDR_A, "beta": ADDR_B},
    )
    session.fit(frame)
    assert session.weights.sum() == pytest.approx(1.0)
    predicted = session.predict(frame.iloc[-5:])
    assert predicted[0] == "predicted"


@patch("orion_finance_sdk_py.lifecycle.validate_order", side_effect=lambda x: {k: 1 for k in x})
@patch("orion_finance_sdk_py.lifecycle.Intent")
def test_intent_session_encrypt(MockIntent, _validate):
    idx = _daily_index(12)
    frame = pd.DataFrame(
        {
            "alpha": np.linspace(0.01, 0.02, 12),
            "beta": np.linspace(-0.01, 0.01, 12),
        },
        index=idx,
    )
    MockIntent.return_value.encrypt.return_value = b"sealed"
    session = IntentSession(
        _FakeEstimator(),
        address_by_label={"alpha": ADDR_A, "beta": ADDR_B},
    )
    session.fit(frame)
    assert session.encrypt() == b"sealed"
    MockIntent.return_value.encrypt.assert_called_once()


@patch("orion_finance_sdk_py.lifecycle.submit_intent")
@patch(
    "orion_finance_sdk_py.lifecycle.validate_order",
    side_effect=lambda x: {checksum_address(ADDR_A): 500_000_000},
)
def test_intent_session_submit(mock_validate, mock_submit):
    idx = _daily_index(12)
    frame = pd.DataFrame(
        {
            "alpha": np.linspace(0.01, 0.02, 12),
            "beta": np.linspace(-0.01, 0.01, 12),
        },
        index=idx,
    )
    mock_submit.return_value = MagicMock(name="tx")
    session = IntentSession(
        _FakeEstimator(),
        vault_address=ADDR_A,
        address_by_label={"alpha": ADDR_A, "beta": ADDR_B},
    )
    session.fit(frame)
    result = session.submit()
    assert result is mock_submit.return_value
    mock_submit.assert_called_once()
    assert mock_submit.call_args.kwargs["vault_address"] == ADDR_A
