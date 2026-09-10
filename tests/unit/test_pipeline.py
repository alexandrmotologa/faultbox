"""Unit tests for ToxicPipeline."""

from __future__ import annotations

import pytest

from faultbox.core.pipeline import ToxicPipeline
from faultbox.toxics.base import BaseToxic, StreamContext, ToxicDirection


class DummyToxic(BaseToxic):
    def __init__(
        self, name: str, suffix: str, direction: ToxicDirection = ToxicDirection.BOTH
    ) -> None:
        super().__init__(name=name, toxic_type="dummy", direction=direction)
        self.suffix = suffix

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        return chunk + self.suffix.encode("utf-8")


class DroppingToxic(BaseToxic):
    def __init__(self, name: str) -> None:
        super().__init__(name=name, toxic_type="drop")

    async def transform(self, chunk: bytes, context: StreamContext) -> bytes | None:
        return None


@pytest.mark.asyncio
async def test_pipeline_chaining() -> None:
    pipeline = ToxicPipeline()
    t1 = DummyToxic(name="t1", suffix="_one")
    t2 = DummyToxic(name="t2", suffix="_two")

    pipeline.add_toxic(t1)
    pipeline.add_toxic(t2)

    assert len(pipeline.list_toxics()) == 2
    assert pipeline.get_toxic("t1") is t1

    ctx = StreamContext(proxy_name="test", direction=ToxicDirection.INBOUND)
    result = await pipeline.process(b"hello", ctx)
    assert result == b"hello_one_two"


@pytest.mark.asyncio
async def test_pipeline_direction_filtering() -> None:
    pipeline = ToxicPipeline()
    t_in = DummyToxic(name="in", suffix="_in", direction=ToxicDirection.INBOUND)
    t_out = DummyToxic(name="out", suffix="_out", direction=ToxicDirection.OUTBOUND)

    pipeline.add_toxic(t_in)
    pipeline.add_toxic(t_out)

    ctx_in = StreamContext(proxy_name="test", direction=ToxicDirection.INBOUND)
    ctx_out = StreamContext(proxy_name="test", direction=ToxicDirection.OUTBOUND)

    res_in = await pipeline.process(b"msg", ctx_in)
    res_out = await pipeline.process(b"msg", ctx_out)

    assert res_in == b"msg_in"
    assert res_out == b"msg_out"


@pytest.mark.asyncio
async def test_pipeline_drop_chunk() -> None:
    pipeline = ToxicPipeline()
    pipeline.add_toxic(DroppingToxic(name="drop"))
    pipeline.add_toxic(DummyToxic(name="t1", suffix="_ignored"))

    ctx = StreamContext(proxy_name="test", direction=ToxicDirection.INBOUND)
    result = await pipeline.process(b"data", ctx)
    assert result is None


def test_pipeline_duplicate_name_error() -> None:
    pipeline = ToxicPipeline()
    t1 = DummyToxic(name="dup", suffix="1")
    t2 = DummyToxic(name="dup", suffix="2")

    pipeline.add_toxic(t1)
    with pytest.raises(ValueError):
        pipeline.add_toxic(t2)


def test_pipeline_remove_and_clear() -> None:
    pipeline = ToxicPipeline()
    t1 = DummyToxic(name="t1", suffix="1")
    pipeline.add_toxic(t1)

    assert pipeline.remove_toxic("t1") is True
    assert pipeline.remove_toxic("non_existent") is False
    assert len(pipeline.list_toxics()) == 0
