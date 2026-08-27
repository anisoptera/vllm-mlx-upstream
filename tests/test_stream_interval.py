# SPDX-License-Identifier: Apache-2.0
"""Streaming must not drop tokens when --stream-interval > 1.

Regression for the GLM-5.2 "word salad" bug: with stream_interval=5 the engine
forwarded only every 5th per-step RequestOutput to the collector and dropped the
4 in between. Since each step's RequestOutput carries only that step's ~1-token
``new_text``, 4 of every 5 tokens' text was silently lost, so streamed output
looked like scrambled fragments (e.g. "1alyze  Count by ...").

The collector already aggregates ``new_text`` on ``put()``; the interval must
gate *notification/release* to the consumer, never drop the accumulated text.
"""

from vllm_mlx.output_collector import RequestOutputCollector, RequestStreamState
from vllm_mlx.request import RequestOutput


def _step(i: int, n: int) -> RequestOutput:
    """A single decode step emitting token ``i`` of ``n`` (text ``"i "``)."""
    return RequestOutput(
        request_id="r",
        new_token_ids=[i],
        new_text=f"{i} ",
        output_token_ids=list(range(1, i + 1)),
        output_text="".join(f"{j} " for j in range(1, i + 1)),
        finished=(i == n),
        finish_reason="stop" if i == n else None,
        completion_tokens=i,
    )


def _drive(n_tokens: int, interval: int):
    """Mimic the engine loop + a consumer draining the collector each step."""
    collector = RequestOutputCollector(aggregate=True)
    state = RequestStreamState(stream_interval=interval)
    received = []
    releases = 0
    for i in range(1, n_tokens + 1):
        out = _step(i, n_tokens)
        send = state.should_send(out.completion_tokens, out.finished)
        collector.put(out, notify=send)
        if send:
            state.mark_sent(out.completion_tokens)
        got = collector.get_nowait()
        if got is not None:
            received.append(got.new_text)
            releases += 1
    return received, releases


def test_no_text_dropped_across_interval():
    expected = "".join(f"{j} " for j in range(1, 13))  # 12 tokens
    received, _ = _drive(12, interval=5)
    assert "".join(received) == expected


def test_interval_batches_releases():
    # 12 tokens, interval 5: releases at token 1 (first), 6, 11, and 12 (finish).
    _, releases = _drive(12, interval=5)
    assert releases == 4


def test_get_nowait_holds_back_until_notified():
    collector = RequestOutputCollector(aggregate=True)
    collector.put(_step(2, 12), notify=False)  # mid-interval, not released yet
    assert collector.get_nowait() is None
    collector.put(_step(3, 12), notify=True)   # interval boundary
    out = collector.get_nowait()
    assert out is not None
    # both the held-back and the boundary token's text are present
    assert out.new_text == "2 3 "


def test_interval_one_releases_every_token():
    received, releases = _drive(5, interval=1)
    assert "".join(received) == "1 2 3 4 5 "
    assert releases == 5
