/** Trusted worker prelude. Package source is appended only inside this realm. */
export const workerPrelude = String.raw`
'use strict';
(() => {
  const send = self.postMessage.bind(self);
  for (const name of ['fetch','XMLHttpRequest','WebSocket','EventSource','Worker','SharedWorker','importScripts','indexedDB','caches']) {
    try { Object.defineProperty(self, name, { value: undefined, configurable: false, writable: false }); } catch {}
  }
  const pending = new Map(), mounts = [], frames = [], actions = [], changes = [];
  let sequence = 0, state = null, ctx = null;
  const fail = error => send({ type: 'failure', code: 'extensions.scriptFailed' });
  const draw = () => {
    if (!state || !ctx || !state.visible) return;
    const { width, height, dpr = 1 } = state;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    try { for (const frame of frames) frame({ ctx, width, height, time: state.reducedMotion ? 0 : performance.now(), theme: state.theme }); } catch (error) { fail(error); }
  };
  Object.defineProperty(self, 'EffiLife', { configurable: false, writable: false, value: Object.freeze({
    onMount(callback) { mounts.push(callback); },
    onFrame(callback) { frames.push(callback); },
    onAction(callback) { actions.push(callback); },
    onChange(callback) { changes.push(callback); },
    render(view) { send({ type: 'render', view }); },
    request(method, params) {
      const id = 'request-' + ++sequence;
      return new Promise((resolve, reject) => { pending.set(id, { resolve, reject }); send({ type: 'request', request: { id, method, params } }); });
    },
  }) });
  self.addEventListener('error', event => { event.preventDefault(); fail(event.error); });
  self.addEventListener('unhandledrejection', event => { event.preventDefault(); fail(event.reason); });
  self.onmessage = async event => {
    const data = event.data;
    if (data.type === 'init') {
      state = data;
      if (data.canvas) { ctx = data.canvas.getContext('2d'); state.canvas = data.canvas; }
      try { for (const mount of mounts) await mount({ ...state, ctx }); } catch (error) { fail(error); return; }
      draw(); send({ type: 'ready' });
    } else if (data.type === 'update' && state) {
      Object.assign(state, data.state);
      if (state.canvas) { state.canvas.width = Math.round(state.width * state.dpr); state.canvas.height = Math.round(state.height * state.dpr); }
      for (const change of changes) { try { change(data.state); } catch (error) { fail(error); } }
      draw();
    } else if (data.type === 'action') {
      try { for (const action of actions) await action(data.action); } catch (error) { fail(error); }
    } else if (data.type === 'response') {
      const callback = pending.get(data.id);
      if (callback) { pending.delete(data.id); data.error ? callback.reject(Object.assign(new Error(data.error), { code: data.error })) : callback.resolve(data.result); }
    }
  };
  setInterval(() => send({ type: 'heartbeat' }), 1000);
  setInterval(() => { if (state && !state.reducedMotion) draw(); }, 1000 / 30);
})();
`

