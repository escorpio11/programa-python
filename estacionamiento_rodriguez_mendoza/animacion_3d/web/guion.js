// Guion del recorrido: tomas de cámara, rótulos y programación de vehículos en movimiento.
// Todo depende solo del tiempo t (segundos) para poder renderizar cuadro a cuadro.

const suave = (x) => x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x);
const suave2 = (x) => { x = Math.min(1, Math.max(0, x)); return x * x * x * (x * (x * 6 - 15) + 10); };
const lerp = (a, b, f) => a + (b - a) * f;

export const RESUMEN = {
  area: '820 m²', plazas: '28', estandar: '26', accesibles: '2', motos: '5 + 2', techado: '414 m²',
  acero: '6.8 t', galibo: '2.80 m', voladizo: '4.55 m', pasillo: '6.50 m',
};
const R = RESUMEN;

export function crearGuion({ datos, camera, overlay, modo, THREE, centroLote, curva, largoCurva }) {
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const C = centroLote.clone();
  const vert = Object.fromEntries(Object.entries(datos.vertices).map(([k, p]) => [k, V(p[0], 0, p[1])]));
  const acc = Object.fromEntries(datos.accesos.map((a) => [a.codigo, a]));
  const P1 = V(acc['P-1'].centro[0], 0, acc['P-1'].centro[1]);
  const P2 = V(acc['P-2'].centro[0], 0, acc['P-2'].centro[1]);
  const in1 = V(acc['P-1'].hacia_adentro[0], 0, acc['P-1'].hacia_adentro[1]);
  const in2 = V(acc['P-2'].hacia_adentro[0], 0, acc['P-2'].hacia_adentro[1]);
  const cobs = Object.fromEntries(datos.coberturas.map((c) => [c.nombre, c]));
  const colT2 = cobs['T-2'].columnas.map((p) => V(p[0], 0, p[2]));
  const colT1 = cobs['T-1'].columnas.map((p) => V(p[0], 0, p[2]));
  const norte = V(datos.meta.norte[0], 0, datos.meta.norte[1]).normalize();

  // posición (arco) de cada portón sobre la curva del recorrido
  const N = 1200;
  const muestras = Array.from({ length: N + 1 }, (_, i) => curva.getPointAt(i / N));
  const arco = (P) => {
    let best = 0, dmin = 1e9;
    muestras.forEach((q, i) => { const d = q.distanceTo(P); if (d < dmin) { dmin = d; best = i; } });
    return best / N * largoCurva;
  };
  const sP1 = arco(P1), sP2 = arco(P2);
  const VEL = 2.8;

  // ---------------- programación de vehículos en movimiento: s(t) = vel * (t - tRef) + sRef
  const programa = [
    { tipo: 'pickup', color: '#f2f2f0', tRef: 13.0, sRef: sP1 },     // entra por P-1 a los 13 s
    { tipo: 'sedan', color: '#8e1b1b', tRef: 53.5, sRef: sP2 },      // sale por P-2 a los 53.5 s (toma exterior de salida)
    { tipo: 'suv', color: '#2b2d30', tRef: 72.0, sRef: sP1 },        // entra durante el cierre
  ];
  const sDe = (p, t) => p.sRef + VEL * (t - p.tRef);
  const posAuto = (i, t) => {
    const s = sDe(programa[i], t);
    const u = Math.min(Math.max(s / largoCurva, 0), 1);
    return { p: curva.getPointAt(u), tg: curva.getTangentAt(u), s };
  };

  // ---------------- tomas
  const tomas = [];
  // corte = true: cambio de plano sin fundido (corte en acción)
  const toma = (t0, t1, fn, rotulo = null, corte = false) => tomas.push({ t0, t1, fn, rotulo, corte });

  // 1. Apertura aérea (órbita alta)
  toma(0, 10, (f) => {
    const a0 = Math.atan2(-0.62, -0.78) + 0.55, a1 = a0 - 0.75;
    const a = lerp(a0, a1, suave(f));
    const r = lerp(92, 74, suave(f)), h = lerp(70, 52, suave(f));
    return { pos: V(C.x + Math.cos(a) * r, h, C.z + Math.sin(a) * r), obj: V(C.x, 0, C.z), fov: 36 };
  }, null);

  // 2. Acceso por la calle lateral: descenso sobre el carril opuesto hacia P-1, con la camioneta entrando
  toma(10, 16.5, (f, t) => {
    const fuera = P1.clone().sub(in1.clone().multiplyScalar(6.5));
    const lado = V(-in1.z, 0, in1.x);           // a lo largo de la calle
    const p0 = fuera.clone().add(lado.clone().multiplyScalar(-16)).setY(15);
    const p1 = fuera.clone().add(lado.clone().multiplyScalar(-5.5)).setY(3.2);
    const pos = p0.clone().lerp(p1, suave2(f));
    const auto = posAuto(0, t).p;
    const obj = P1.clone().setY(1.6).lerp(auto.clone().setY(1.2), 0.45);
    return { pos, obj, fov: lerp(42, 48, f) };
  }, { n: '01', titulo: 'Ingreso por la calle lateral', sub: 'Portón corredizo de 3.00 m · la espera no ocupa el Jr. Rodríguez de Mendoza' });

  // 3. Seguimiento del auto por los pasillos: la cámara recorre la misma trayectoria, detrás y en alto
  const enCurva = (s) => curva.getPointAt(Math.min(Math.max(s / largoCurva, 0), 1));
  toma(16.5, 27, (f, t) => {
    const s = sDe(programa[0], t);
    const p = enCurva(s);
    const pos = enCurva(s - lerp(11, 9.5, f)).setY(lerp(7.0, 5.6, suave(f)));
    const obj = enCurva(s + 3).setY(0.5).lerp(p, 0.45);
    return { pos, obj, fov: 50 };
  }, { n: '02', titulo: 'Circulación en un solo sentido', sub: `Pasillos de ${R.pasillo} · ${R.estandar} plazas de 2.50 × 5.00 m y ${R.accesibles} accesibles de 3.80 × 5.00 m` }, true);

  // 4. Bajo la cobertura T-1: travelling oblicuo a la fila A (ritmo columna - 3 plazas - columna)
  toma(27, 38, (f) => {
    const a = colT1[0], b = colT1[3];
    const dirF = b.clone().sub(a).normalize();
    const haciaPasillo = V(-0.9839, 0, 0.1786);
    const base = a.clone().lerp(b, lerp(-0.05, 0.40, suave(f)));
    const pos = base.clone().addScaledVector(haciaPasillo, 8.0).setY(1.8);
    const obj = base.clone().addScaledVector(dirF, 8).addScaledVector(haciaPasillo, 0.8).setY(2.3);
    return { pos, obj, fov: 52 };
  }, { n: '03', titulo: 'Una columna cada 3 plazas', sub: `Voladizo de ${R.voladizo}: plazas y pasillos libres de columnas`, lado: 'der' });

  // 5. Detalle estructural: grúa diagonal desde el pasillo B hacia una columna de T-2
  toma(38, 46.5, (f) => {
    const col = colT2[2];
    const pos = col.clone().add(V(lerp(5.5, 3.2, suave(f)), 0, lerp(-8.2, -6.4, suave(f)))).setY(lerp(1.2, 2.2, suave(f)));
    const obj = col.clone().add(V(-1.6, 0, -1.2)).setY(lerp(1.6, 3.3, suave(f)));
    return { pos, obj, fov: 56 };
  }, { n: '04', titulo: 'Estructura metálica ligera', sub: `${R.acero} de acero · vigas reticuladas · gálibo libre de ${R.galibo} (camionetas y combis)`, lado: 'der' });

  // 6. Salida por P-2 vista desde el Jr. Rodríguez de Mendoza: el sedán sale y gira hacia B
  toma(46.5, 56, (f, t) => {
    const lado = V(-in2.z, 0, in2.x);           // a lo largo del jirón, hacia B
    const pos = P2.clone().addScaledVector(in2, -7.0).addScaledVector(lado, lerp(-15, -12.5, suave(f))).setY(lerp(3.4, 2.5, suave(f)));
    const auto = posAuto(1, t).p.setY(1.0);
    const obj = P2.clone().setY(1.6).addScaledVector(lado, 2.0).lerp(auto, 0.3);
    return { pos, obj, fov: 46 };
  }, { n: '05', titulo: 'Salida a Jr. Rodríguez de Mendoza', sub: 'Portón de 3.00 m con línea de PARE · puerta peatonal independiente' });

  // 7. Vista en planta (ascenso a cenital, cubierta translúcida): el lote se corre para no quedar bajo el rótulo
  toma(56, 66, (f) => {
    const giro = lerp(0.0, 0.35, f);
    const T = V(C.x - 4, 0, C.z + 7);
    const r = lerp(30, 6, suave(f));
    const pos = V(T.x + Math.sin(giro) * r, lerp(40, 78, suave(f)), T.z + Math.cos(giro) * r);
    return { pos, obj: T, fov: 38 };
  }, { n: '06', titulo: 'Distribución general', sub: `${R.area} de terreno · ${R.plazas} plazas techadas (${R.accesibles} accesibles) · 5 motos y 2 mototaxis` });

  // 8. Cierre: órbita amplia
  toma(66, 80, (f) => {
    const a0 = Math.atan2(-0.82, -0.57) - 0.9, a1 = a0 + 0.8;
    const a = lerp(a0, a1, f);
    const r = lerp(60, 85, suave(f)), h = lerp(30, 46, suave(f));
    const pos = V(C.x + Math.cos(a) * r, h, C.z + Math.sin(a) * r);
    // el objetivo se adelanta para que el proyecto quede en la mitad inferior, bajo la tarjeta de cierre
    const adelante = V(C.x - pos.x, 0, C.z - pos.z).normalize().multiplyScalar(lerp(4, 22, suave((f - 0.05) / 0.35)));
    return { pos, obj: V(C.x, 1, C.z).add(adelante), fov: 38 };
  }, null);

  // Opacidad de la cubierta TR-4: se vuelve translúcida durante la planta para leer la distribución
  const tP = tomas[6];
  const opacidadTecho = (t) => {
    if (t < tP.t0 || t >= tP.t1) return 1;
    return 1 - 0.8 * suave((t - tP.t0 - 2.0) / 1.5) * (1 - suave((t - (tP.t1 - 1.9)) / 1.4));
  };
  const tC = tomas[7].t0 + 3.5;              // entrada de la tarjeta de cierre

  const duracion = 80;

  // ---------------- rótulos (HTML)
  overlay.innerHTML = `
  <style>
    #ov * { box-sizing: border-box; }
    #ov { position:absolute; inset:0; font-family: Inter, "Liberation Sans", Arial, sans-serif; color:#fff; }
    #ov .sup { position:absolute; left:0; right:0; top:0; height:18%; background:linear-gradient(180deg, rgba(5,10,18,.45), rgba(5,10,18,0)); }
    #ov .marca { position:absolute; top:4.2%; left:4%; display:flex; align-items:center; gap:14px; opacity:.92; }
    #ov .marca .p { width:44px; height:44px; border-radius:9px; background:#1f5fa8; display:grid; place-items:center;
      font-weight:800; font-size:26px; box-shadow:0 2px 10px rgba(0,0,0,.25); }
    #ov .marca .t1 { font-weight:700; font-size:17px; letter-spacing:.16em; text-transform:uppercase; text-shadow:0 1px 6px rgba(0,0,0,.45); }
    #ov .marca .t2 { font-size:14px; letter-spacing:.06em; opacity:.85; text-shadow:0 1px 6px rgba(0,0,0,.45); }
    #ov .rot { position:absolute; left:4%; bottom:7.5%; max-width:56%; padding:18px 26px 20px 24px;
      background:linear-gradient(90deg, rgba(10,18,30,.78), rgba(10,18,30,.42)); border-left:5px solid #f2b705;
      border-radius:4px; backdrop-filter: blur(2px); }
    #ov .rot.der { left:auto; right:4%; bottom:10.5%; text-align:right; border-left:0; border-right:5px solid #f2b705;
      background:linear-gradient(270deg, rgba(10,18,30,.78), rgba(10,18,30,.42)); padding:18px 24px 20px 26px; }
    #ov .rot .n { font-size:15px; font-weight:700; letter-spacing:.22em; color:#f2b705; }
    #ov .rot .ti { font-size:38px; font-weight:750; margin-top:6px; letter-spacing:-.01em; }
    #ov .rot .su { font-size:20px; margin-top:8px; opacity:.92; line-height:1.35; }
    #ov .cartel { position:absolute; inset:0; display:flex; flex-direction:column; justify-content:flex-start; align-items:center;
      text-align:center; padding-top:7.5%; background:linear-gradient(180deg, rgba(8,14,24,.72) 0%, rgba(8,14,24,.42) 32%, rgba(8,14,24,0) 60%); }
    #ov .cartel .k { font-size:18px; letter-spacing:.32em; color:#f2b705; font-weight:700; }
    #ov .cartel .h { font-size:66px; font-weight:800; letter-spacing:-.01em; margin-top:14px; text-shadow:0 4px 30px rgba(0,0,0,.45); }
    #ov .cartel .s { font-size:24px; margin-top:12px; opacity:.95; text-shadow:0 2px 14px rgba(0,0,0,.5); }
    #ov .cartel .linea { width:120px; height:4px; background:#f2b705; margin:26px auto 0; border-radius:2px; }
    #ov .datos { display:flex; gap:44px; margin-top:34px; }
    #ov .datos div { text-align:center; } #ov .datos b { display:block; font-size:44px; font-weight:800; }
    #ov .datos b { text-shadow:0 2px 12px rgba(0,0,0,.5); }
    #ov .datos span { font-size:17px; letter-spacing:.14em; text-transform:uppercase; opacity:.9; text-shadow:0 1px 6px rgba(0,0,0,.6); }
    #ov .negro { position:absolute; inset:0; background:#000; }
    #ov .pie { position:absolute; right:4%; bottom:4.2%; font-size:15px; letter-spacing:.12em; opacity:.7; text-transform:uppercase;
      text-shadow:0 1px 4px rgba(0,0,0,.65); }
  </style>
  <div id="ov">
    <div class="sup" id="sup"></div>
    <div class="marca"><div class="p">P</div><div><div class="t1">Estacionamiento techado</div>
      <div class="t2">Jr. Rodríguez de Mendoza · San Nicolás (Mendoza), Amazonas</div></div></div>
    <div class="rot" id="rot"><div class="n" id="rn"></div><div class="ti" id="rt"></div><div class="su" id="rs"></div></div>
    <div class="cartel" id="titulo"><div class="k">ANTEPROYECTO · OCTUBRE 2026</div>
      <div class="h">Estacionamiento vehicular techado</div>
      <div class="s">Jr. Rodríguez de Mendoza esq. calle lateral · San Nicolás (Mendoza), Amazonas</div><div class="linea"></div></div>
    <div class="cartel" id="cierre"><div class="k">RESUMEN DEL PROYECTO</div>
      <div class="h">Estacionamiento vehicular techado</div>
      <div class="datos"><div><b>${R.area}</b><span>terreno</span></div><div><b>${R.plazas}</b><span>plazas techadas</span></div>
        <div><b>${R.techado}</b><span>área techada</span></div><div><b>${R.motos}</b><span>motos y mototaxis</span></div>
        <div><b>${R.galibo}</b><span>gálibo libre</span></div></div>
      <div class="s" style="margin-top:30px;font-size:20px">Ingreso por calle lateral · salida a Jr. Rodríguez de Mendoza · estructura metálica en voladizo</div></div>
    <div class="pie">Visualización de anteproyecto · referencial</div>
    <div class="negro" id="negro"></div>
  </div>`;
  // los rótulos se diseñaron para 900 px de alto: se escalan con la ventana (1080p -> 1.2)
  const ov = overlay.querySelector('#ov');
  const escalar = () => { ov.style.zoom = (Math.max(overlay.clientHeight || 900, 360) / 900).toFixed(4); };
  escalar();
  window.addEventListener('resize', escalar);
  const el = (id) => overlay.querySelector('#' + id);
  const rot = el('rot'), rn = el('rn'), rt = el('rt'), rs = el('rs'), titulo = el('titulo'), cierre = el('cierre'), negro = el('negro');
  const marca = overlay.querySelector('.marca'), pie = overlay.querySelector('.pie');
  const visible = (e, o, dy = 0) => { e.style.opacity = o.toFixed(3); e.style.transform = `translateY(${dy.toFixed(1)}px)`; e.style.display = o <= 0.001 ? 'none' : ''; };
  let rotuloActual = null;

  function aplicar(t) {
    const tc = Math.min(Math.max(t, 0), duracion - 1e-3);
    const tm = tomas.find((s) => tc >= s.t0 && tc < s.t1) || tomas[tomas.length - 1];
    const f = (tc - tm.t0) / (tm.t1 - tm.t0);
    const c = tm.fn(f, tc);
    camera.fov = c.fov;
    camera.position.copy(c.pos);
    camera.lookAt(c.obj);
    camera.near = c.pos.y > 15 ? 2.0 : 0.25;     // más precisión de profundidad en las tomas aéreas
    camera.updateProjectionMatrix();

    if (modo === 'still') { overlay.style.display = 'none'; return; }
    overlay.style.display = '';
    // fundidos: inicio, cortes entre tomas y final
    let negroO = 0;
    if (tc < 1.2) negroO = 1 - suave(tc / 1.2);
    for (const s of tomas.slice(1)) {
      if (s.corte) continue;
      const d = tc - s.t0, FD = 0.5;
      if (d > -FD && d < FD) negroO = Math.max(negroO, 1 - Math.abs(d) / FD);
    }
    if (tc > duracion - 1.6) negroO = Math.max(negroO, suave((tc - (duracion - 1.6)) / 1.4));
    visible(negro, negroO);
    // título de apertura
    const ot = suave((tc - 1.2) / 1.0) * (1 - suave((tc - 7.6) / 1.2));
    visible(titulo, ot, (1 - suave((tc - 1.2) / 1.0)) * 12);
    // cierre
    const oc = suave((tc - tC) / 1.4) * (1 - suave((tc - (duracion - 1.0)) / 0.8));
    visible(cierre, oc, (1 - suave((tc - tC) / 1.4)) * 12);
    // marca superior
    visible(marca, Math.max(0, suave((tc - 9) / 1) - oc));
    visible(el('sup'), Math.max(0, suave((tc - 9) / 1) - oc));
    visible(pie, Math.max(0, suave((tc - 9) / 1) - oc) * 0.7);
    // rótulo de la toma
    if (tm.rotulo) {
      if (rotuloActual !== tm.rotulo) {
        rn.textContent = tm.rotulo.n; rt.textContent = tm.rotulo.titulo; rs.textContent = tm.rotulo.sub; rotuloActual = tm.rotulo;
        rot.classList.toggle('der', tm.rotulo.lado === 'der');
      }
      const d0 = tc - tm.t0, d1 = tm.t1 - tc;
      const o = suave((d0 - 0.6) / 0.7) * suave((d1 - 0.3) / 0.6);
      visible(rot, o, (1 - suave((d0 - 0.6) / 0.7)) * 16);
    } else visible(rot, 0);
  }

  return { duracion, aplicar, programa, sDe, VEL, sP1, sP2, opacidadTecho };
}
