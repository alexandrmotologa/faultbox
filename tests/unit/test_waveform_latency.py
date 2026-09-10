"""Unit tests for WaveformLatencyToxic."""

from __future__ import annotations

import pytest

from faultbox.toxics import StreamContext, ToxicDirection, WaveformLatencyToxic, create_toxic


@pytest.fixture
def context() -> StreamContext:
    return StreamContext(proxy_name="test", direction=ToxicDirection.BOTH)


def test_sine_waveform_calculation() -> None:
    toxic = WaveformLatencyToxic(
        name="sine_test",
        base_latency_ms=100,
        amplitude_ms=200,
        period_sec=10.0,
        waveform="sine",
        jitter_ms=0,
    )
    start = toxic._start_time

    # At t=0s, phase = 0, sin(0) = 0 -> (0+1)/2 = 0.5 -> 100 + 200*0.5 = 200ms
    val_0 = toxic.calculate_current_latency_ms(now=start)
    assert pytest.approx(val_0, 0.1) == 200.0

    # At t=2.5s (phase=0.25), sin(pi/2) = 1 -> factor = 1.0 -> 100 + 200*1 = 300ms (peak)
    val_peak = toxic.calculate_current_latency_ms(now=start + 2.5)
    assert pytest.approx(val_peak, 0.1) == 300.0

    # At t=7.5s (phase=0.75), sin(3pi/2) = -1 -> factor = 0.0 -> 100 + 200*0 = 100ms (trough)
    val_trough = toxic.calculate_current_latency_ms(now=start + 7.5)
    assert pytest.approx(val_trough, 0.1) == 100.0


def test_sawtooth_waveform_calculation() -> None:
    toxic = WaveformLatencyToxic(
        name="saw_test",
        base_latency_ms=50,
        amplitude_ms=100,
        period_sec=10.0,
        waveform="sawtooth",
        jitter_ms=0,
    )
    start = toxic._start_time

    # At t=0s, latency = 50 + 100*0.0 = 50ms
    assert pytest.approx(toxic.calculate_current_latency_ms(now=start), 0.1) == 50.0

    # At t=5.0s (halfway), latency = 50 + 100*0.5 = 100ms
    assert pytest.approx(toxic.calculate_current_latency_ms(now=start + 5.0), 0.1) == 100.0

    # At t=9.9s (near peak), latency = 50 + 100*0.99 = 149ms
    assert pytest.approx(toxic.calculate_current_latency_ms(now=start + 9.9), 1.0) == 149.0


def test_burst_waveform_calculation() -> None:
    toxic = WaveformLatencyToxic(
        name="burst_test",
        base_latency_ms=100,
        amplitude_ms=500,
        period_sec=10.0,
        waveform="burst",
        jitter_ms=0,
    )
    start = toxic._start_time

    # At t=5.0s (50% phase < 80%), latency = 100ms
    assert toxic.calculate_current_latency_ms(now=start + 5.0) == 100.0

    # At t=8.5s (85% phase >= 80%), latency = 100 + 500 = 600ms
    assert toxic.calculate_current_latency_ms(now=start + 8.5) == 600.0


def test_brownian_waveform_bounds() -> None:
    toxic = WaveformLatencyToxic(
        name="brownian_test",
        base_latency_ms=50,
        amplitude_ms=100,
        waveform="brownian",
        jitter_ms=0,
    )

    # Sample 50 steps and ensure all stay bounded in [50, 150]
    for _ in range(50):
        val = toxic.calculate_current_latency_ms()
        assert 50.0 <= val <= 150.0


@pytest.mark.asyncio
async def test_waveform_latency_transform(context: StreamContext) -> None:
    toxic = WaveformLatencyToxic(
        name="wave_run",
        base_latency_ms=10,
        amplitude_ms=5,
        waveform="sine",
    )
    res = await toxic.transform(b"ping", context)
    assert res == b"ping"


def test_waveform_factory_creation() -> None:
    t = create_toxic(
        name="dyn_wave",
        toxic_type="waveform_latency",
        attributes={"base_latency_ms": 120, "waveform": "sawtooth"},
    )
    assert isinstance(t, WaveformLatencyToxic)
    assert t.base_latency_ms == 120
    assert t.waveform == "sawtooth"
