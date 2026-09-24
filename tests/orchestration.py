"""Exercise runner failure/timeout handling without running scientific children."""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from unittest.mock import patch

source=Path(__file__).resolve().parents[1]/'reproduce.py'
spec=importlib.util.spec_from_file_location('runner_under_test',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def run_control(timeout=False):
    old=Path.cwd()
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); (root/'inputs').mkdir(); (root/'results').mkdir()
        (root/'inputs/cases.json').write_text('[{"id":"B01"}]')
        (root/'inputs/fixed-codebooks.json').write_text('[]')
        (root/'inputs/anchor-pam3.json').write_text('{}')
        (root/'inputs/selection.json').write_text('{"candidate_count_per_pass":1,"pilot_candidate_count":0}')
        (root/'results/campaign.json').write_text('{"complete_locked_case_replay":true}')
        outcome=subprocess.CompletedProcess(['mock'],2,'','controlled failure')
        effect=subprocess.TimeoutExpired(['mock'],module.CHILD_TIMEOUT_SECONDS) if timeout else None
        try:
            with patch.object(module,'ROOT',root), patch.object(sys,'argv',['reproduce.py']), \
                 patch.object(module.subprocess,'run',return_value=outcome,side_effect=effect), \
                 contextlib.redirect_stdout(io.StringIO()):
                try: module.main()
                except (RuntimeError,subprocess.TimeoutExpired): pass
                else: raise AssertionError('failure was not propagated')
            report=json.loads((root/'results/campaign.json').read_text())
            assert report['complete_locked_case_replay'] is False
            assert report['status']==('timeout' if timeout else 'failed')
        finally:
            import os; os.chdir(old)



def run_limit_control():
    """Verify that the documented 3 GiB address-space limit is applied."""
    calls=[]
    with patch.object(module.resource,'setrlimit',side_effect=lambda kind,value: calls.append((kind,value))):
        module.set_child_limits()
    expected=(module.CHILD_ADDRESS_SPACE_BYTES,module.CHILD_ADDRESS_SPACE_BYTES)
    assert calls==[(module.resource.RLIMIT_AS,expected)]

if __name__=='__main__':
    run_control();run_control(timeout=True);run_limit_control()
    print('Two fail-closed runner controls and the 3 GiB resource-limit assertion passed; no scientific child executed.')
