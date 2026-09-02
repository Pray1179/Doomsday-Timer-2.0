/* Character catalogue search + filters (explore/characters.html).
   Runs immediately; guards on element existence so it's a no-op elsewhere. */
(function () {
  var grid = document.getElementById('cat-grid');
  var input = document.getElementById('catalogue-search');
  if (!grid || !input) return;

  var cards = [].slice.call(grid.querySelectorAll('.cat-card'));
  var clearBtn = document.getElementById('catalogue-clear');
  var state = { uni: null, team: null, type: null, q: '' };

  // Pre-stamp a searchable text blob per card (name, alias, actor, team, tags).
  cards.forEach(function (c) { c.setAttribute('data-search', c.textContent); });

  // Team names are whitespace-joined in data-team; split for matching.
  function teamMatch(cardTeams, team) {
    return cardTeams.split(' ').indexOf(team) !== -1;
  }

  function apply() {
    var q = state.q.toLowerCase();
    cards.forEach(function (card) {
      var ok = true;
      if (state.uni && card.getAttribute('data-uni') !== state.uni) ok = false;
      if (ok && state.team && !teamMatch(card.getAttribute('data-team'), state.team)) ok = false;
      if (ok && state.type && card.getAttribute('data-type') !== state.type) ok = false;
      if (ok && q) {
        var hay = (card.getAttribute('data-search') || '').toLowerCase();
        if (hay.indexOf(q) === -1) ok = false;
      }
      card.style.display = ok ? '' : 'none';
    });
    var shown = cards.filter(function (c) { return c.style.display !== 'none'; }).length;
    var label = document.getElementById('cat-count');
    if (label) label.textContent = shown + ' of ' + cards.length + ' characters';
  }

  // Filter chips: buttons with data-uni / data-team / data-type act as toggles.
  function wireChips(attr, slot) {
    var btns = [].slice.call(document.querySelectorAll('button.pill[data-' + attr + ']'));
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var val = b.getAttribute('data-' + attr);
        btns.forEach(function (x) { x.classList.remove('on'); });
        if (state[slot] === val) { state[slot] = null; }
        else { state[slot] = val; b.classList.add('on'); }
        apply();
      });
    });
  }
  wireChips('uni', 'uni');
  wireChips('team', 'team');
  wireChips('type', 'type');

  input.addEventListener('input', function () {
    state.q = input.value;
    apply();
  });

  if (clearBtn) clearBtn.addEventListener('click', function () {
    state = { uni: null, team: null, type: null, q: '' };
    input.value = '';
    [].slice.call(document.querySelectorAll('button.pill.on')).forEach(function (x) {
      x.classList.remove('on');
    });
    apply();
  });

  apply();

  // Staggered entrance reveal. When unsupported or reduced-motion, we never
  // add .js-animate, so the CSS default keeps every card visible instantly.
  var animate = true;
  if (!('IntersectionObserver' in window)) animate = false;
  if (animate && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) animate = false;
  if (animate) {
    grid.classList.add('js-animate');
    var seen = 0;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        el.style.transitionDelay = Math.min(seen, 8) * 32 + 'ms';
        seen += 1;
        // Once the entrance transition ends, clear the inline delay so the
        // hover lift isn't staggered afterward.
        el.addEventListener('transitionend', function once(e) {
          if (e.propertyName === 'opacity') {
            el.style.transitionDelay = '';
            el.removeEventListener('transitionend', once);
          }
        });
        el.classList.add('in');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px 120px 0px' });
    cards.forEach(function (c) { io.observe(c); });
  }
})();