// Comprobación mínima y offline: que clip-data.js y el script incrustado en
// discovery-screening-clip.html sean JavaScript válido y que las duraciones
// sumen lo que dice la lámina. No abre un navegador: solo analiza.
//
//   node validate_clip.js

const fs = require("fs");
const path = require("path");

const dir = __dirname;
const datos = fs.readFileSync(path.join(dir, "clip-data.js"), "utf8");
const html = fs.readFileSync(path.join(dir, "discovery-screening-clip.html"), "utf8");

const contexto = { window: {} };
new Function("window", datos)(contexto.window);
const D = contexto.window.CLIP_DATA;

const bloques = html.match(/<script>[\s\S]*?<\/script>/g) || [];
const inline = bloques.map((b) => b.replace(/^<script>/, "").replace(/<\/script>$/, ""));
inline.forEach((codigo, i) => {
  new Function(codigo);
  console.log(`script incrustado ${i + 1}: sintaxis OK (${codigo.split("\n").length} líneas)`);
});

const total = D.pasos.reduce((s, p) => s + p.dur, 0);
console.log(`pasos: ${D.pasos.length}`);
console.log(`duración total: ${total} s = ${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`);
console.log(`registros: ${D.registros.length}, sin verificar: ${D.registros.filter((r) => !r.verificado).length}`);
console.log(`decisiones: ${D.decisiones.map((d) => d.veredicto).join(" / ")}`);

const ids = new Set(D.registros.map((r) => r.id));
D.decisiones.forEach((d) => {
  if (!ids.has(d.registro)) throw new Error(`decisión sin registro: ${d.registro}`);
  d.marcas.forEach((m) => {
    if (!D.criterios.some((c) => c.clave === m.clave)) {
      throw new Error(`marca con criterio inexistente: ${m.clave}`);
    }
  });
});

const vistas = new Set(D.pasos.map((p) => p.vista));
["pregunta", "criterios", "consulta", "candidatos", "decision", "resultado", "limites", "cierre"]
  .forEach((v) => { if (!vistas.has(v)) throw new Error(`falta la vista ${v} en pasos`); });

const revelados = D.pasos.filter((p) => p.vista === "candidatos").map((p) => p.revelar);
if (revelados.length !== D.registros.length) {
  throw new Error(`pasos de candidatos (${revelados.length}) != registros (${D.registros.length})`);
}

console.log("referencias cruzadas: OK");
