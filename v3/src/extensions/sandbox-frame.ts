/** Only this trusted relay runs on the iframe DOM thread; package code stays in a Worker. */
export const framePrelude = String.raw`
(() => {
  let connected = false;
  addEventListener('message', function connect(event) {
    if (connected || event.source !== parent || event.data !== 'effilife-connect' || event.ports.length !== 1) return;
    connected = true;
    removeEventListener('message', connect);
    const port = event.ports[0], canvas = document.getElementById('canvas'), view = document.getElementById('view');
    let worker, url, allowed = [], userStyle, failed = false, count = 0, windowStart = 0;
    const send = value => port.postMessage(value);
    const safeCss = source => {
      const css = String(source || '').replace(/\/\*[\s\S]*?\*\//g, '');
      if (/[\\<>]|url\s*\(|image-set\s*\(|@import|expression\s*\(/i.test(css)) throw new Error('css');
      return css;
    };
    const tags = new Set('div span p strong em small b i u h1 h2 h3 h4 h5 h6 main section article header footer nav aside ul ol li dl dt dd table thead tbody tfoot tr th td caption button label input textarea select option optgroup form fieldset legend details summary progress meter output br hr pre code time'.split(' '));
    const attributes = new Set('class id role for type value name checked selected disabled placeholder min max step tabindex rows cols multiple required autocomplete title datetime'.split(' '));
    function clean(node) {
      if (node.nodeType === Node.TEXT_NODE) return document.createTextNode(node.textContent);
      if (node.nodeType !== Node.ELEMENT_NODE || !tags.has(node.localName)) return document.createTextNode('');
      const element = document.createElement(node.localName);
      for (const attribute of node.attributes) {
        if (!attributes.has(attribute.name) && !/^(aria|data)-[a-z0-9-]+$/.test(attribute.name)) continue;
        if (attribute.name === 'type' && !['text','number','checkbox','radio','button','submit','reset','email','password','search','tel','url','date','time','datetime-local','range','color'].includes(attribute.value)) continue;
        element.setAttribute(attribute.name, attribute.value);
      }
      for (const child of node.childNodes) element.append(clean(child));
      return element;
    }
    function render(data) {
      if (!allowed.includes('app.layout') || !data || typeof data.html !== 'string') return;
      if (data.html.length > 1048576 || String(data.css || '').length > 262144) throw new Error('view');
      const css = safeCss(data.css);
      const parsed = new DOMParser().parseFromString(data.html, 'text/html');
      const fragment = document.createDocumentFragment();
      for (const node of parsed.body.childNodes) fragment.append(clean(node));
      view.replaceChildren(fragment);
      if (!userStyle) {
        userStyle = document.createElement('style');
        userStyle.nonce = document.currentScript?.nonce || document.querySelector('script[nonce]').nonce;
        document.head.append(userStyle);
      }
      userStyle.textContent = css;
    }
    view.addEventListener('click', event => {
      const target = event.target.closest('[data-action]');
      if (target && target.tagName !== 'FORM') worker?.postMessage({ type: 'action', action: { type: 'click', name: target.dataset.action, value: target.value } });
    });
    view.addEventListener('submit', event => {
      event.preventDefault();
      if (event.target.dataset.action) worker?.postMessage({ type: 'action', action: { type: 'submit', name: event.target.dataset.action, values: Object.fromEntries(new FormData(event.target).entries()) } });
    });
    port.onmessage = event => {
      const data = event.data;
      if (data.type === 'init' && !worker) {
        allowed = data.capabilities;
        url = URL.createObjectURL(new Blob([data.source], { type: 'text/javascript' }));
        worker = new Worker(url);
        worker.onmessage = event => {
          if (failed) return;
          if (Date.now() - windowStart > 1000) { windowStart = Date.now(); count = 0; }
          if (++count > 120) { failed = true; worker.terminate(); send({ type: 'failure', code: 'extensions.requestLimit' }); return; }
          const message = event.data;
          if (message?.type === 'render') {
            try { render(message.view); } catch { send({ type: 'failure', code: 'extensions.scriptFailed' }); }
          } else send(message);
        };
        worker.onerror = event => { event.preventDefault(); send({ type: 'failure', code: 'extensions.scriptFailed' }); };
        const state = { ...data.state, type: 'init' };
        if (allowed.includes('overlay.canvas') || allowed.includes('overlay.interactive')) {
          if (!canvas.transferControlToOffscreen) { send({ type: 'failure', code: 'extensions.unsupportedCanvas' }); return; }
          canvas.width = Math.round(state.width * state.dpr); canvas.height = Math.round(state.height * state.dpr);
          state.canvas = canvas.transferControlToOffscreen();
          worker.postMessage(state, [state.canvas]);
        } else worker.postMessage(state);
      } else if (data.type === 'dispose') {
        worker?.terminate(); if (url) URL.revokeObjectURL(url); port.close();
      } else worker?.postMessage(data);
    };
    port.start();
    send({ type: 'connected' });
  });
})();
`

export function sandboxDocument(nonce: string): string {
  const policy = "default-src 'none'; script-src 'nonce-" + nonce + "'; style-src 'nonce-" + nonce + "'; worker-src blob:; connect-src 'none'; img-src 'none'; font-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none';"
  return '<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + policy + '"><style nonce="' + nonce + '">html,body{margin:0;width:100%;min-height:100%;background:transparent;color:inherit;font:15px/1.6 system-ui,sans-serif}#canvas{position:fixed;inset:0;width:100%;height:100%;pointer-events:none}#view{position:relative}*{box-sizing:border-box}</style></head><body><canvas id="canvas"></canvas><div id="view"></div><script nonce="' + nonce + '">' + framePrelude + '</script></body></html>'
}

