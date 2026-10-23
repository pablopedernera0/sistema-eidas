// Apps Script (script.google.com) para mandar devoluciones con PDF adjunto desde la cuenta del docente.
// Usado en el cierre 2c-2026 (81 mails). Pasos: subir la carpeta a Drive, crearBorradores, revisar, enviarBorradores.
//
// crearBorradores: crea en Gmail un BORRADOR por estudiante (no envía nada) con su PDF adjunto.
// Lee la carpeta de Drive "envio-cierre-2c-2026" (mails.json + pdfs/).
// Los mails de ITI que faltan se buscan en la lista de estudiantes del Classroom de ITI-21.
// Requiere el servicio avanzado "Google Classroom API" (Servicios → +).

const CARPETA = 'envio-cierre-2c-2026';  // carpeta en Drive con mails.json + pdfs/
const CURSO_ITI = '796542799761';

function norm(s) {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase()
    .replace(/[^A-Z ]/g, ' ').replace(/\s+/g, ' ').trim();
}

function rosterITI() {
  const lista = [];
  let token;
  do {
    const r = Classroom.Courses.Students.list(CURSO_ITI, { pageToken: token, pageSize: 100 });
    (r.students || []).forEach(s => lista.push({
      nombre: norm(s.profile.name.familyName + ' ' + s.profile.name.givenName),
      mail: s.profile.emailAddress,
    }));
    token = r.nextPageToken;
  } while (token);
  return lista;
}

// Apellido completo + primer nombre tienen que aparecer, y en un solo estudiante del curso.
function buscarMail(roster, alumno) {
  const [ap, nom] = alumno.split(',');
  const tokens = norm(ap).split(' ').concat(norm(nom).split(' ')[0]);
  const hits = roster.filter(r => tokens.every(t => r.nombre.split(' ').includes(t)));
  return hits.length === 1 ? hits[0].mail : '';
}

function crearBorradores() {
  const dirs = DriveApp.getFoldersByName(CARPETA);
  if (!dirs.hasNext()) throw new Error('No encuentro la carpeta ' + CARPETA + ' en Drive');
  const dir = dirs.next();
  const mails = JSON.parse(dir.getFilesByName('mails.json').next().getBlob().getDataAsString('UTF-8'));
  const pdfs = dir.getFoldersByName('pdfs').next();
  const props = PropertiesService.getScriptProperties();
  const hechos = JSON.parse(props.getProperty('hechos') || '{}');
  const log = [];
  const t0 = Date.now();
  let roster = null;
  for (const m of mails) {
    const clave = m.materia + '|' + m.alumno;
    if (hechos[clave]) continue;
    if (Date.now() - t0 > 5 * 60 * 1000) { log.push('Corte por tiempo: ejecutá de nuevo para seguir.'); break; }
    let to = m.to;
    if (!to) {
      roster = roster || rosterITI();
      to = buscarMail(roster, m.alumno);
      log.push((to ? 'Mail de Classroom: ' + to + ' ← ' : 'SIN MAIL (completalo a mano): ') + m.alumno);
    }
    const opciones = { htmlBody: m.html };
    if (m.pdf) opciones.attachments = [pdfs.getFilesByName(m.pdf).next().getBlob().setName(m.filename)];
    GmailApp.createDraft(to, m.subject, m.text, opciones);
    hechos[clave] = true;
    props.setProperty('hechos', JSON.stringify(hechos));
  }
  log.push(Object.keys(hechos).length + ' de ' + mails.length + ' borradores creados.');
  Logger.log(log.join('\n'));
}

// Solo si hay que volver a crear todo desde cero (antes borrar los borradores viejos).
function reiniciar() {
  PropertiesService.getScriptProperties().deleteProperty('hechos');
}

// Envía los borradores con estos asuntos. Gmail corta si se mandan muchos seguidos
// ("No se permite la operación en Gmail"): la pausa evita el corte y, si igual pasa,
// volver a ejecutar sigue con los que quedaron como borrador.
const ASUNTOS = [
  'Diseño de Sistemas Web — Nota final del cuatrimestre',
  'Infraestructura de Redes II — Nota final del cuatrimestre',
];

function enviarBorradores() {
  let enviados = 0;
  const sinDestinatario = [];
  for (const d of GmailApp.getDrafts()) {
    const m = d.getMessage();
    if (!ASUNTOS.includes(m.getSubject())) continue;
    if (!m.getTo()) { sinDestinatario.push(m.getSubject()); continue; }
    d.send();
    enviados++;
    Utilities.sleep(3000);
  }
  Logger.log(enviados + ' enviados' + (sinDestinatario.length ? ' · sin destinatario: ' + sinDestinatario.length : ''));
}

function cuota() {
  Logger.log(MailApp.getRemainingDailyQuota());
}
