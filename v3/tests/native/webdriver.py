"""Small W3C WebDriver client shared by Linux WebKit and native host tests."""
from pathlib import Path
import base64
import json
import time
import urllib.error
import urllib.request

ELEMENT = "element-6066-11e4-a52e-4f735466cecf"

class Driver:
    def __init__(self, endpoint, capabilities):
        self.endpoint = endpoint.rstrip("/")
        self.session = self.request("POST", "/session", {"capabilities": {"alwaysMatch": capabilities}})["sessionId"]
        self.call("POST", "/timeouts", {"implicit": 0, "pageLoad": 30000, "script": 15000})

    def request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(self.endpoint + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                result = json.load(response).get("value")
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode()) from error
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(str(result))
        return result

    def call(self, method, path, payload=None):
        return self.request(method, "/session/" + self.session + path, payload)

    def script(self, source, *args):
        return self.call("POST", "/execute/sync", {"script": source, "args": list(args)})

    def navigate(self, url):
        self.call("POST", "/url", {"url": url})

    def wait(self, predicate, message="WebView condition", seconds=12):
        deadline = time.monotonic() + seconds
        last = None
        while time.monotonic() < deadline:
            try:
                value = predicate()
                if value:
                    return value
            except RuntimeError as error:
                last = error
            time.sleep(0.1)
        raise AssertionError(message + (": " + str(last) if last else ""))

    def element(self, selector):
        return self.call("POST", "/element", {"using": "css selector", "value": selector})

    def click(self, element):
        self.call("POST", "/element/" + element[ELEMENT] + "/click", {})

    def button(self, text, scope="document"):
        node = self.wait(lambda: self.script("return Array.from(" + scope + ".querySelectorAll('button')).find(e => e.textContent.trim() === arguments[0] && e.getClientRects().length) || null", text), "button " + text)
        self.click(node)

    def field(self, label, scope="document"):
        return self.wait(lambda: self.script("return Array.from(" + scope + ".querySelectorAll('label')).find(e => e.querySelector('span')?.textContent.trim() === arguments[0])?.querySelector('input,textarea,select') || null", label), "field " + label)

    def fill(self, element, value):
        self.call("POST", "/element/" + element[ELEMENT] + "/clear", {})
        self.call("POST", "/element/" + element[ELEMENT] + "/value", {"text": value})

    def file(self, element, path: Path):
        self.call("POST", "/element/" + element[ELEMENT] + "/value", {"text": str(path.resolve())})

    def screenshot(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(self.call("GET", "/screenshot")))

    def close(self):
        self.call("DELETE", "")

