// Desglose de triángulos / mallas del entorno (para ajustar el presupuesto)
import { servir, abrir } from '../servidor.mjs';
const PUERTO = 8772;
const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho: 800, alto: 450, modo: 'still', puerto: PUERTO, pagina: 'pruebas/entorno.html' });
const r = await page.evaluate(() => {
  const out = []; let tot = 0;
  window.APP.entorno.grupo.traverse((o) => {
    if (!(o.isMesh || o.isLine)) return;
    const g = o.geometry; const n = g.index ? g.index.count : g.attributes.position.count;
    const inst = o.isInstancedMesh ? o.count : 1;
    const t = o.isMesh ? n / 3 * inst : 0; tot += t;
    out.push([o.name, Math.round(t), inst, o.castShadow, g.attributes.position.count]);
  });
  out.sort((a, b) => b[1] - a[1]);
  return { tot, out, casas: window.APP.entorno.grupo.userData.casas };
});
console.log('total', r.tot, 'casas', r.casas);
for (const x of r.out) console.log(x.join('\t'));
if (errores.length) console.log('ERRORES:\n' + errores.slice(0, 10).join('\n'));
await browser.close(); srv.close();
