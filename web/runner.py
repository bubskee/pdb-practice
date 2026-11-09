"""Browser adapter around real CPython unittest and pdb."""
import contextlib
import importlib
import io
import json
import linecache
import os
import pathlib
import runpy
import shlex
import sys
import time
import traceback
import unittest

sys.dont_write_bytecode = True
ROOT = '/usercode/FILESYSTEM'
os.makedirs(ROOT, exist_ok=True)
sys.path.insert(0, ROOT)
_known_files = set()


def prepare(files):
    global _known_files
    os.chdir(ROOT)
    for name, module in list(sys.modules.items()):
        filename = getattr(module, '__file__', '') or ''
        if filename.startswith(ROOT + '/'):
            sys.modules.pop(name, None)
    for filename in _known_files - set(files):
        path = pathlib.Path(ROOT, filename)
        if path.is_file():
            path.unlink()
    for filename, content in files.items():
        path = pathlib.Path(ROOT, filename)
        if not path.resolve().is_relative_to(pathlib.Path(ROOT)):
            raise ValueError('File outside exercise directory')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    _known_files = set(files)
    importlib.invalidate_caches()
    linecache.clearcache()
    import bdb
    import pdb
    bdb.Breakpoint.clearBreakpoints()
    pdb.Pdb._last_pdb_instance = None
    sys.breakpointhook = sys.__breakpointhook__


def run_request(request):
    prepare(request['files'])
    entries = []
    capture = io.StringIO()
    started = time.perf_counter()
    mode = request.get('mode', 'structured')
    original_result = unittest.TextTestRunner.resultclass
    original_argv = sys.argv[:]

    class Result(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            self.current = {'id':test.id(), 'status':'pass', 'detail':''}

        def problem(self, test, status, detail):
            if getattr(self, 'current', {}).get('id') == test.id():
                self.current['status'] = status
                self.current['detail'] += detail
            else:
                entries.append({'id':test.id(), 'status':status, 'detail':detail})

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.problem(test, 'fail', self._exc_info_to_string(err, test))

        def addError(self, test, err):
            super().addError(test, err)
            self.problem(test, 'error', self._exc_info_to_string(err, test))

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.problem(test, 'skip', reason)

        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err)
            self.problem(test, 'skip', 'Expected failure')

        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test)
            self.problem(test, 'fail', 'Unexpected success')

        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            if err:
                self.problem(test, 'fail' if issubclass(err[0], test.failureException) else 'error',
                             str(subtest) + '\n' + self._exc_info_to_string(err, test))

        def stopTest(self, test):
            entries.append(dict(self.current))
            super().stopTest(test)

    unittest.TextTestRunner.resultclass = Result
    exit_code = 0
    try:
        if mode == 'structured':
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                loader = unittest.TestLoader()
                suite = (loader.loadTestsFromName(request['test']) if request.get('test')
                         else loader.discover('tests', pattern='*Tests.py', top_level_dir=ROOT))
                result = unittest.TextTestRunner(verbosity=2).run(suite)
                exit_code = 0 if result.wasSuccessful() else 1
        else:
            args = shlex.split(request['command'])
            if not args:
                return {'tests':[], 'count':0, 'exit':0, 'seconds':0, 'output':''}
            if args in (['bash', 'main.sh'], ['sh', 'main.sh'], ['./main.sh']):
                args = ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', '*Tests.py', '-v']
            command = args.pop(0)
            if command in ('python', 'python3'):
                if not args:
                    import code
                    code.interact(local={'__name__':'__console__'})
                elif args[0] in ('--version', '-V'):
                    print('Python ' + sys.version.split()[0])
                elif args[0] == '-m' and len(args) >= 2:
                    sys.argv = [args[1]] + args[2:]
                    runpy.run_module(args[1], run_name='__main__', alter_sys=True)
                elif args[0] == '-c' and len(args) >= 2:
                    sys.argv = ['-c'] + args[2:]
                    exec(compile(args[1], '<string>', 'exec'), {'__name__':'__main__'})
                elif not args[0].startswith('-'):
                    sys.argv = args
                    runpy.run_path(args[0], run_name='__main__')
                else:
                    raise ValueError('Supported Python forms: -m module, -c code, script.py, or interactive python3')
            elif command == 'pwd':
                print(os.getcwd())
            elif command == 'ls':
                print('\n'.join(sorted(os.listdir(args[0] if args else '.'))))
            elif command == 'cat' and args:
                for name in args:
                    print(pathlib.Path(name).read_text(), end='')
            else:
                print('This browser terminal supports python3, ls, cat, pwd, clear, and bash main.sh.\n'
                      'It runs real Python/pdb, with a limited command launcher rather than a full OS shell.')
                exit_code = 127
    except SystemExit as error:
        exit_code = error.code if isinstance(error.code, int) else int(bool(error.code))
    except BaseException:
        exit_code = 1
        if mode == 'structured':
            capture.write(traceback.format_exc())
        else:
            traceback.print_exc()
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.settrace(None)
        sys.argv = original_argv
        unittest.TextTestRunner.resultclass = original_result
    return {'tests':entries, 'count':len(entries), 'exit':exit_code,
            'seconds':time.perf_counter()-started, 'output':capture.getvalue()}
