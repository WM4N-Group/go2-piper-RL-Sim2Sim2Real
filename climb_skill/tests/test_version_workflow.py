"""验证版本切换不会覆盖未保存源码、已保存分支或训练产物。"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class VersionWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.root = self.repo/'climb_skill'
        self.root.mkdir()
        (self.root/'scripts').mkdir()
        shutil.copy2(Path(__file__).resolve().parents[1]/'scripts/manage.py', self.root/'scripts/manage.py')
        self.git('init', '-b', 'codex/test')
        self.git('config', 'user.name', 'test')
        self.git('config', 'user.email', 'test@localhost')
        (self.root/'.gitignore').write_text('outputs/\n')
        (self.root/'VERSION.json').write_text(json.dumps({'version':'V1'}))
        (self.root/'source.txt').write_text('V1')
        (self.root/'scripts/train.py').write_text('import time\nprint("ready", flush=True)\ntime.sleep(60)\n')
        self.git('add','-A');self.git('commit','-m','baseline');self.git('tag','climb/V1')
        (self.root/'source.txt').write_text('V3')
        self.git('add','-A');self.git('commit','-m','later');self.git('tag','climb/V3')
        (self.root/'outputs').mkdir()
        (self.root/'outputs/model.pt').write_bytes(b'unchanged model')

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL,text=True)

    def manage(self,*args):
        return subprocess.run([sys.executable,str(self.root/'scripts/manage.py'),*args],capture_output=True,text=True)

    def test_dirty_refusal_save_and_switch_preserve_artifacts(self):
        (self.root/'source.txt').write_text('my draft')
        self.assertNotEqual(self.manage('switch','V1').returncode,0)
        self.assertEqual((self.root/'source.txt').read_text(),'my draft')
        result=self.manage('save','V3-draft','--message','save draft')
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertEqual(self.manage('switch','V1').returncode,0)
        self.assertEqual((self.root/'source.txt').read_text(),'V1')
        self.assertNotEqual(self.manage('switch','V3-draft').returncode,0)
        self.assertEqual(self.manage('save','restored-V1','--message','restore').returncode,0)
        self.assertEqual(self.manage('switch','V3-draft').returncode,0)
        self.assertEqual((self.root/'source.txt').read_text(),'my draft')
        self.assertEqual((self.root/'outputs/model.pt').read_bytes(),b'unchanged model')
        self.assertNotEqual(self.manage('save','V1','--message','must not overwrite').returncode,0)

    def test_running_training_blocks_switch(self):
        process=subprocess.Popen([sys.executable,str(self.root/'scripts/train.py')],stdout=subprocess.PIPE,text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(),'ready')
            self.assertNotEqual(self.manage('switch','V1').returncode,0)
            self.assertEqual((self.root/'source.txt').read_text(),'V3')
        finally:
            process.terminate();process.wait(timeout=5);process.stdout.close()
