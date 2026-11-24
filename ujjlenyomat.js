(() => {
  const MAG = parseInt("__MAG__", 16) >>> 0;
  const rnd = (i) => {
    let x = (MAG ^ Math.imul(i + 1, 0x9e3779b1)) >>> 0;
    x ^= x << 13; x ^= x >>> 17; x ^= x << 5;
    return (x >>> 0) / 4294967296;
  };
  const rejt = (obj, nev, fn) => {
    const eredeti = obj[nev];
    if (!eredeti) return;
    const uj = fn(eredeti);
    Object.defineProperty(uj, "toString", { value: () => eredeti.toString() });
    try { Object.defineProperty(obj, nev, { value: uj, writable: true, configurable: true }); } catch (e) {}
  };
  const getter = (proto, nev, ertek) => {
    try { Object.defineProperty(proto, nev, { get: () => ertek, configurable: true }); } catch (e) {}
  };

  const zajosit = (adat) => {
    const d = adat.data;
    for (let i = 0; i < d.length; i += 4) {
      if (rnd(i) < 0.02) d[i] = d[i] ^ 1;
    }
    return adat;
  };

  rejt(CanvasRenderingContext2D.prototype, "getImageData", (eredeti) => function (...a) {
    return zajosit(eredeti.apply(this, a));
  });

  const masolat = (vaszon) => {
    const ctx = vaszon.getContext && vaszon.getContext("2d");
    if (!ctx || !vaszon.width || !vaszon.height) return vaszon;
    const m = document.createElement("canvas");
    m.width = vaszon.width; m.height = vaszon.height;
    const mc = m.getContext("2d");
    mc.drawImage(vaszon, 0, 0);
    mc.putImageData(zajosit(CanvasRenderingContext2D.prototype.getImageData.call(mc, 0, 0, m.width, m.height)), 0, 0);
    return m;
  };
  rejt(HTMLCanvasElement.prototype, "toDataURL", (eredeti) => function (...a) {
    return eredeti.apply(masolat(this), a);
  });
  rejt(HTMLCanvasElement.prototype, "toBlob", (eredeti) => function (...a) {
    return eredeti.apply(masolat(this), a);
  });

  const glParam = (eredeti) => function (p) {
    if (p === 37445) return "Google Inc.";
    if (p === 37446) return "ANGLE (Generic GPU)";
    return eredeti.call(this, p);
  };
  if (window.WebGLRenderingContext) rejt(WebGLRenderingContext.prototype, "getParameter", glParam);
  if (window.WebGL2RenderingContext) rejt(WebGL2RenderingContext.prototype, "getParameter", glParam);

  if (window.AudioBuffer) {
    rejt(AudioBuffer.prototype, "getChannelData", (eredeti) => function (...a) {
      const d = eredeti.apply(this, a);
      if (!d.__arnyek) {
        for (let i = 0; i < d.length; i += 97) d[i] += (rnd(i) - 0.5) * 1e-7;
        try { Object.defineProperty(d, "__arnyek", { value: true }); } catch (e) {}
      }
      return d;
    });
  }

  getter(Navigator.prototype, "hardwareConcurrency", 4);
  getter(Navigator.prototype, "deviceMemory", 8);
  getter(Navigator.prototype, "doNotTrack", null);
  getter(Navigator.prototype, "globalPrivacyControl", true);
  try { delete Navigator.prototype.getBattery; } catch (e) {}
  getter(Screen.prototype, "colorDepth", 24);
  getter(Screen.prototype, "pixelDepth", 24);
})();
