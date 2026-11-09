import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v0.29.0/full/pyodide.mjs';
let python, input, interrupts, interactive = false;
const decoder = new TextDecoder();
const output = {write(buffer) {
  self.postMessage({type:'output', text:decoder.decode(buffer, {stream:true})});
  return buffer.length;
}, isatty:true};
self.onmessage = async ({data}) => {
  if (data.type === 'init') {
    try {
      input = data.input ? new Int32Array(data.input) : null;
      interrupts = data.interrupts ? new Uint8Array(data.interrupts) : null;
      python = await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.29.0/full/'});
      python.setStdout(output); python.setStderr(output);
      if (interrupts) python.setInterruptBuffer(interrupts);
      python.setStdin({isatty:true, stdin: () => {
        if (!interactive || !input) throw new Error('Interactive input requires Terminal mode and browser isolation.');
        Atomics.store(input, 0, 0);
        self.postMessage({type:'stdin'});
        while (Atomics.load(input, 0) === 0) {
          Atomics.wait(input, 0, 0, 100); python.checkInterrupt();
        }
        if (Atomics.load(input, 0) === -1) return null;
        // TextDecoder requires an ordinary buffer, not a SharedArrayBuffer view.
        return new TextDecoder().decode(new Uint8Array(input.buffer, 8, Atomics.load(input, 1)).slice());
      }});
      const response = await fetch('runner.py');
      if (!response.ok) throw new Error('Could not load Python runner');
      python.runPython(await response.text());
      self.postMessage({type:'ready',version:python.runPython('sys.version.split()[0]')});
    } catch(error) {self.postMessage({type:'error',error:String(error),init:true});}
    return;
  }
  try {
    interactive = data.mode === 'terminal';
    if (interrupts) interrupts[0] = 0;
    python.globals.set('_request_json', JSON.stringify(data));
    const value = python.runPython('json.dumps(run_request(json.loads(_request_json)))');
    self.postMessage({type:'result',result:JSON.parse(value)});
  } catch(error) {self.postMessage({type:'error',error:String(error)});}
};
