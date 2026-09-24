/* Eigener Seiten- und Klickzaehler fuer geisburgrecords.com.
 *
 * Gegenstueck: geisburg-pipeline/apps_script/webstats.gs (Auswertung ueber die
 * trackwerk-Web-App, action=statsreport). Bewusst ohne Fremddienst: GoatCounter zeigte
 * bis 05.09.2026 auf einen Account, den es nie gab, es wurde also nie etwas gezaehlt.
 *
 * Erhoben werden nur Pfad, Ereignis, Ziel-Domain und die Herkunfts-Domain. Keine IP,
 * kein Fingerprint, keine Cookies, kein localStorage - deshalb ohne Einwilligung
 * zulaessig und ohne Banner. Der Token in der URL ist oeffentlich und berechtigt nur
 * zum Anhaengen einer Zeile im Statistik-Sheet.
 */
(function () {
  var STATS = 'https://script.google.com/macros/s/AKfycbwY8N1v8O_fxnK5_En_FlNklsynvnTjid59Gkeae_lEhmu7HjkrlEkyWfivlMkjU6ACKw/exec?s=gbr-stats-2026';

  function hit(ereignis, ziel) {
    try {
      var b = new Blob([JSON.stringify({
        p: location.pathname, e: ereignis, t: ziel || '', r: document.referrer || ''
      })], {type: 'text/plain'});
      navigator.sendBeacon(STATS, b);   // feuert und vergisst, blockiert nie einen Klick
    } catch (err) {}
  }

  hit('pageview');

  // Nur Klicks, die von der Seite wegfuehren. Interne Navigation zaehlt der Seitenaufruf
  // der Zielseite ohnehin, sonst stuende jeder Klick zweimal in der Statistik.
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
    if (!a || !a.href) return;
    if (a.hostname && a.hostname !== location.hostname) {
      hit('click', a.hostname.replace(/^www\./, '').slice(0, 60));
    }
  }, true);
})();
