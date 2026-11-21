#!/usr/bin/env python3
"""data/words.json → docs/index.html (үгсийн картуудыг харах хуудас, GitHub Pages-д тохиромжтой)."""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
words = json.load(open(os.path.join(ROOT, 'data', 'words.json'), encoding='utf-8'))
os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)

data = json.dumps(words, ensure_ascii=False).replace('</', '<\\/')
page = """<!DOCTYPE html>
<html lang="mn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ЭЕШ Арена — Үгсийн сан</title>
<style>
:root{--bg:#F7F7F5;--card:#fff;--ink:#1F2A30;--muted:#6B7780;--line:#E4E7EA;--acc:#FF9600;--kw:#1CB0F6}
@media (prefers-color-scheme:dark){:root{--bg:#131F24;--card:#1B2B34;--ink:#F1F7FA;--muted:#93A5B1;--line:#37464F}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:2;background:var(--bg);padding:16px 20px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;flex-wrap:wrap}
h1{font-size:20px;margin:0 auto 0 0}input,select{font:inherit;padding:8px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:20px;max-width:1400px;margin:auto}
.c{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.img{aspect-ratio:1;background:var(--line);display:flex;align-items:center;justify-content:center;text-align:center;color:var(--muted);font-size:12px;padding:16px}
.img img{width:100%;height:100%;object-fit:cover}
.b{padding:14px 16px;display:flex;flex-direction:column;gap:6px}
.top{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.w{font-size:24px;font-weight:800}.id{margin-left:auto;color:var(--muted);font-size:12px}
.pos{font-size:12px;color:var(--muted)}.pr{color:var(--muted)}.m{font-size:18px;font-weight:700;color:var(--acc)}
.mn{background:color-mix(in srgb,var(--kw) 10%,transparent);border-radius:10px;padding:8px 10px}
.kw{color:var(--kw);font-weight:700}.ex{font-size:14px;color:var(--muted)}.ex b{color:var(--ink);font-weight:600}
.flip{cursor:pointer}.hide .m,.hide .mn,.hide .ex{filter:blur(6px)}
</style></head><body>
<header><h1>Үгсийн сан · <span id="n"></span> үг</h1>
<input id="q" placeholder="Хайх (англи эсвэл монгол)…">
<select id="p"><option value="">Бүх аймаг</option><option value="noun">нэр үг</option><option value="verb">үйл үг</option><option value="adjective">тэмдэг нэр</option></select>
<label><input type="checkbox" id="h"> Утгыг нуух (давтлага)</label></header>
<main id="g"></main>
<script>
const W=""" + data + """;
const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function hl(s,k){const i=s.toLowerCase().indexOf(k.toLowerCase().slice(0,3));if(i<0)return esc(s);
 let j=i;while(j<s.length&&/[А-Яа-яЁёӨөҮүA-Za-z0-9]/.test(s[j]))j++;return esc(s.slice(0,i))+'<span class="kw">'+esc(s.slice(i,j))+'</span>'+esc(s.slice(j));}
function card(w){return `<div class="c flip" onclick="this.classList.toggle('hide')">
 <div class="img"><img src="../${w.image.file}" alt="${esc(w.word)}" onerror="this.parentNode.textContent='Зураг хараахан үүсээгүй'"></div>
 <div class="b"><div class="top"><span class="w">${esc(w.word)}</span><span class="pr">${esc(w.ipa)} · ${esc(w.pron_mn)}</span><span class="id">#${w.id}</span></div>
 <div class="pos">${w.pos_mn.join(', ')}</div><div class="m">${esc(w.meaning_mn)}</div>
 <div class="mn">🔑 <span class="kw">${esc(w.keyword_mn)}</span> — ${hl(w.mnemonic_mn,w.keyword_mn)}</div>
 <div class="ex"><b>${esc(w.example.en)}</b><br>${esc(w.example.mn)}</div></div></div>`}
function draw(){const q=document.getElementById('q').value.trim().toLowerCase(),p=document.getElementById('p').value,h=document.getElementById('h').checked;
 const L=W.filter(w=>(!p||w.pos.includes(p))&&(!q||w.word.toLowerCase().includes(q)||w.meaning_mn.toLowerCase().includes(q)));
 document.getElementById('n').textContent=L.length;const g=document.getElementById('g');g.innerHTML=L.map(card).join('');
 if(h)g.querySelectorAll('.c').forEach(c=>c.classList.add('hide'));}
['q','p','h'].forEach(id=>document.getElementById(id).addEventListener('input',draw));draw();
</script></body></html>"""
open(os.path.join(ROOT, 'docs', 'index.html'), 'w', encoding='utf-8').write(page)
print(f'✓ docs/index.html ({len(words)} үг)')
