/* Character catalogue search, quick groups, pagination, and filters (explore/characters.html).
   Runs immediately; guards on element existence so it's a no-op elsewhere. */
(function () {
  var grid = document.getElementById('cat-grid');
  var input = document.getElementById('catalogue-search');
  if (!grid || !input) return;

  var cards = [].slice.call(grid.querySelectorAll('.cat-card'));
  var clearBtn = document.getElementById('catalogue-clear');
  var quickPills = [].slice.call(document.querySelectorAll('.cat-quick-pill'));
  var prevBtn = document.getElementById('cat-page-prev');
  var nextBtn = document.getElementById('cat-page-next');
  var numsContainer = document.getElementById('cat-page-nums');
  var pageCountLabel = document.getElementById('cat-page-count');
  var totalCountLabel = document.getElementById('cat-count');

  var PAGE_SIZE = 24;
  var state = { uni: null, team: null, type: null, q: '', quick: 'all', page: 1 };

  // Pre-stamp a searchable text blob per card (name, alias, actor, team, tags).
  cards.forEach(function (c) { c.setAttribute('data-search', c.textContent); });

  // Team names are '|'-delimited in data-team; split for exact matching.
  function teamMatch(cardTeams, team) {
    return cardTeams.split('|').indexOf(team) !== -1;
  }

  function matchesCard(card, q) {
    // Quick filter check
    if (state.quick === 'doomsday' && card.getAttribute('data-doomsday') !== '1') return false;
    if (state.quick === 'mcu' && card.getAttribute('data-uni') !== 'MCU') return false;
    if (state.quick === 'xmen' && card.getAttribute('data-uni') !== 'X-Men') return false;
    if (state.quick === 'ff' && card.getAttribute('data-uni') !== 'Fantastic Four') return false;
    if (state.quick === 'spidey') {
      var tags = card.getAttribute('data-tags') || '';
      var uni = card.getAttribute('data-uni') || '';
      if (tags.indexOf('spider-man') === -1 && uni.indexOf('Raimi') === -1 && uni.indexOf('Webb') === -1 && uni.indexOf('SSU') === -1) {
        return false;
      }
    }
    if (state.quick === 'legacy') {
      var tags = card.getAttribute('data-tags') || '';
      if (tags.indexOf('multiverse') === -1 && tags.indexOf('legacy') === -1 && tags.indexOf('blade') === -1 && tags.indexOf('ghost-rider') === -1 && tags.indexOf('punisher') === -1) {
        return false;
      }
    }

    if (state.uni && card.getAttribute('data-uni') !== state.uni) return false;
    if (state.team && !teamMatch(card.getAttribute('data-team') || '', state.team)) return false;
    if (state.type && card.getAttribute('data-type') !== state.type) return false;
    if (q) {
      var hay = (card.getAttribute('data-search') || '').toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }
    return true;
  }

  function renderPagination(totalMatching, totalPages) {
    if (!numsContainer) return;
    numsContainer.innerHTML = '';

    if (totalPages <= 1) {
      if (prevBtn) prevBtn.style.display = 'none';
      if (nextBtn) nextBtn.style.display = 'none';
      return;
    }
    if (prevBtn) prevBtn.style.display = '';
    if (nextBtn) nextBtn.style.display = '';

    if (prevBtn) prevBtn.disabled = state.page <= 1;
    if (nextBtn) nextBtn.disabled = state.page >= totalPages;

    for (var i = 1; i <= totalPages; i++) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'cat-page-num' + (i === state.page ? ' active' : '');
      btn.textContent = i;
      btn.setAttribute('data-page', i);
      (function (p) {
        btn.addEventListener('click', function () {
          if (state.page === p) return;
          state.page = p;
          apply();
          grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      })(i);
      numsContainer.appendChild(btn);
    }
  }

  function apply() {
    var q = state.q.toLowerCase().trim();
    var matching = cards.filter(function (card) {
      return matchesCard(card, q);
    });

    var totalMatching = matching.length;
    var totalPages = Math.max(1, Math.ceil(totalMatching / PAGE_SIZE));
    if (state.page > totalPages) state.page = 1;
    if (state.page < 1) state.page = 1;

    var startIdx = (state.page - 1) * PAGE_SIZE;
    var endIdx = Math.min(startIdx + PAGE_SIZE, totalMatching);

    // Hide all cards first, then show current page slice
    cards.forEach(function (card) { card.style.display = 'none'; });
    for (var i = startIdx; i < endIdx; i++) {
      matching[i].style.display = '';
    }

    if (pageCountLabel) {
      if (totalMatching === 0) {
        pageCountLabel.textContent = 'No matching characters found';
      } else {
        pageCountLabel.textContent = 'Showing ' + (startIdx + 1) + '–' + endIdx + ' of ' + totalMatching + ' characters (Page ' + state.page + ' of ' + totalPages + ')';
      }
    }

    if (totalCountLabel) {
      totalCountLabel.textContent = totalMatching + ' of ' + cards.length + ' characters';
    }

    renderPagination(totalMatching, totalPages);
  }

  // Quick category pills
  quickPills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      quickPills.forEach(function (p) { p.classList.remove('active'); });
      pill.classList.add('active');
      state.quick = pill.getAttribute('data-quick') || 'all';
      state.page = 1;
      apply();
    });
  });

  if (prevBtn) {
    prevBtn.addEventListener('click', function () {
      if (state.page > 1) {
        state.page--;
        apply();
        grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      state.page++;
      apply();
      grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
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
        state.page = 1;
        apply();
      });
    });
  }
  wireChips('uni', 'uni');
  wireChips('team', 'team');
  wireChips('type', 'type');

  input.addEventListener('input', function () {
    state.q = input.value;
    state.page = 1;
    apply();
  });

  if (clearBtn) clearBtn.addEventListener('click', function () {
    state = { uni: null, team: null, type: null, q: '', quick: 'all', page: 1 };
    input.value = '';
    [].slice.call(document.querySelectorAll('button.pill.on')).forEach(function (x) {
      x.classList.remove('on');
    });
    quickPills.forEach(function (p) {
      p.classList.toggle('active', p.getAttribute('data-quick') === 'all');
    });
    apply();
  });

  apply();

  // Staggered entrance reveal
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
