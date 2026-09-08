import io

from memory_eval import progress


def test_progress_always_rewrites_one_terminal_line(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(progress.sys, "stdout", stream)

    reporter = progress.ProgressReporter("Retrieval", 2)
    reporter.advance(item_id="first", status="ok")
    before_finish = stream.getvalue()
    reporter.advance(item_id="second", status="ok")

    assert before_finish.count(progress._REWRITE_LINE) == 2
    assert "\r" not in before_finish
    assert "\n" not in before_finish
    assert stream.getvalue().count(progress._REWRITE_LINE) == 3
    assert stream.getvalue().endswith("\n")
    assert "ok=2 failed=0" in stream.getvalue()


def test_progress_distinguishes_processed_failures(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(progress.sys, "stdout", stream)

    reporter = progress.ProgressReporter("Answer", 2)
    reporter.advance(item_id="first", status="completed")
    reporter.advance(item_id="second", status="FAILED:LLMRequestError")

    assert "2/2" in stream.getvalue()
    assert "ok=1 failed=1" in stream.getvalue()


def test_progress_heartbeat_refreshes_without_advancing(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr(progress.sys, "stdout", stream)

    reporter = progress.ProgressReporter("Answer", 3, completed=2)
    reporter.start_heartbeat(interval=60.0)
    before_close = stream.getvalue()
    reporter.close()

    assert before_close.count(progress._REWRITE_LINE) == 2
    assert "2/3" in before_close
    assert "status=running" in before_close
    assert "\n" not in before_close
