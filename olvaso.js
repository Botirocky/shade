(() => {
  if (document.documentElement.dataset.arnyekOlvaso) { location.reload(); return; }
  const hossz = (el) => [...el.querySelectorAll("p")].reduce((n, p) => n + p.innerText.trim().length, 0);
  let legjobb = document.querySelector("article");
  if (!legjobb || hossz(legjobb) < 400) {
    const pont = new Map();
    for (const p of document.querySelectorAll("p")) {
      const n = p.innerText.trim().length;
      if (n < 40) continue;
      let el = p.parentElement;
      for (const suly of [1, 0.6, 0.3]) {
        if (!el || el === document.body) break;
        pont.set(el, (pont.get(el) || 0) + n * suly);
        el = el.parentElement;
      }
    }
    let max = 0;
    for (const [el, n] of pont) if (n > max) { max = n; legjobb = el; }
  }
  if (!legjobb) return;
  const cim = (document.querySelector("h1") || {}).innerText || document.title;
  const tiszta = document.createElement("div");
  for (const el of legjobb.querySelectorAll("p, h2, h3, h4, ul, ol, blockquote, pre, figure, img")) {
    if (el.closest("figure") && el.tagName === "IMG") continue;
    if (el.parentElement.closest("ul, ol, blockquote, pre, figure") && el.parentElement.closest("ul, ol, blockquote, pre, figure") !== el) continue;
    const m = el.cloneNode(true);
    for (const x of m.querySelectorAll("script, style, iframe, button, form, svg")) x.remove();
    for (const x of [m, ...m.querySelectorAll("*")]) {
      for (const a of [...x.attributes]) if (!["href", "src", "alt", "srcset"].includes(a.name)) x.removeAttribute(a.name);
    }
    if (m.innerText.trim() || m.querySelector("img") || m.tagName === "IMG") tiszta.appendChild(m);
  }
  const perc = Math.max(1, Math.round(tiszta.innerText.split(/\s+/).length / 220));
  const forras = location.hostname.replace(/^www\./, "");
  document.documentElement.dataset.arnyekOlvaso = "1";
  const eredetiCim = document.title;
  document.head.innerHTML = `<meta charset="utf-8"><style>
    :root { color-scheme: dark }
    body { background: #111214; color: #d9d9dc; font: 19px/1.7 Charter, "Iowan Old Style", Georgia, serif; margin: 0; padding: 64px 24px 128px }
    main { max-width: 680px; margin: 0 auto }
    .meta { font: 12px "JetBrains Mono", monospace; color: #6b6d74; margin-bottom: 16px }
    h1 { font: 500 36px/1.2 Inter, sans-serif; color: #e8e8ea; margin: 0 0 40px }
    h2, h3, h4 { font: 500 22px/1.3 Inter, sans-serif; color: #e8e8ea; margin: 40px 0 12px }
    p { margin: 0 0 20px }
    a { color: #e8e8ea; text-decoration-color: #d0583f; text-underline-offset: 3px }
    img { max-width: 100%; height: auto; border-radius: 8px; margin: 12px 0 }
    figure { margin: 24px 0 } figcaption { font: 13px Inter, sans-serif; color: #6b6d74 }
    blockquote { border-left: 2px solid #d0583f; margin: 24px 0; padding-left: 20px; color: #a3a4aa }
    pre { font: 14px "JetBrains Mono", monospace; background: #17181b; padding: 16px; border-radius: 8px; overflow: auto }
  </style>`;
  document.title = eredetiCim;
  document.body.removeAttribute("class");
  document.body.removeAttribute("style");
  document.body.innerHTML = `<main><div class="meta">${forras} · ${perc} perc olvasás</div><h1></h1></main>`;
  document.querySelector("h1").textContent = cim;
  document.querySelector("main").appendChild(tiszta);
  window.scrollTo(0, 0);
})();
