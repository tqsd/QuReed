"""Run the project's numerical/GUI contracts and record reproducible test evidence."""
import contextlib
import importlib.metadata
import io
import json
import platform
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from .project import ROOT


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT/"tests"), pattern="test_*.py")
    report = io.StringIO()
    started = time.perf_counter()
    with contextlib.redirect_stdout(report), contextlib.redirect_stderr(report):
        outcome = unittest.TextTestRunner(stream=report, verbosity=2, buffer=True).run(suite)
    text = report.getvalue()
    out = ROOT/"results"/"verification"
    out.mkdir(parents=True, exist_ok=True)
    (out/"tests.log").write_text(text, encoding="utf-8")
    record = dict(date_utc=datetime.now(timezone.utc).isoformat(),
                  status="PASS" if outcome.wasSuccessful() else "FAIL",
                  tests_run=outcome.testsRun, failures=len(outcome.failures),
                  errors=len(outcome.errors), skipped=len(outcome.skipped),
                  elapsed_s=time.perf_counter()-started,
                  python=sys.version, platform=platform.platform(),
                  versions={p:importlib.metadata.version(p) for p in
                            ("qureed","photon-weave","numpy","scipy","matplotlib","flet","flet-runtime")},
                  caveat="Numerical consistency and native GUI contracts; not experimental validation.")
    (out/"test-report.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2))
    if not outcome.wasSuccessful():
        print(text)
    return 0 if outcome.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
