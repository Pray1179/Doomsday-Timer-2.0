/* Doomsday Fan Hub — Main JS */

(function() {
  'use strict';

  // === CONFIG ===
  const RELEASE_DATE = new Date('2026-12-17T00:01:00'); // Dec 17, 2026 at 12:01 AM
  const UNITS = ['Avengers', 'X-Men', 'Fantastic Four', 'Wakandans', 'New Avengers', 'Villain'];

  // Per-faction quote pools (homepage). Picking a side rotates THAT side's
  // quotes only — never a mixed mash-up.
  const QUOTE_POOLS = {
    default: [
      { line: 'I am inevitable.', src: '— Thanos' },
      { line: 'I am Iron Man.', src: '— Tony Stark' },
      { line: 'Avengers… assemble.', src: '— Steve Rogers' },
    ],
    avengers: [
      { line: 'I can do this all day.', src: '— Steve Rogers' },
      { line: 'Avengers… assemble.', src: '— Steve Rogers' },
      { line: 'Whatever it takes.', src: '— Natasha Romanoff' },
      { line: 'I am Iron Man.', src: '— Tony Stark' },
      { line: 'Part of the journey is the end.', src: '— Tony Stark' },
      { line: 'I’m always angry.', src: '— Bruce Banner' },
    ],
    xmen: [
      { line: 'To me, my X-Men.', src: '— Charles Xavier' },
      { line: 'I’m the best there is at what I do… and what I do best isn’t very nice.', src: '— Wolverine' },
      { line: 'Mutant and proud.', src: '— Ororo Munroe' },
      { line: 'Trust me, you don’t want it to be me.', src: '— Wolverine' },
      { line: 'You are a god among insects. Never let anyone tell you different.', src: '— Erik Lehnsherr' },
    ],
    fantastic: [
      { line: 'Flame on!', src: '— Johnny Storm' },
      { line: 'It’s clobberin’ time!', src: '— Ben Grimm' },
      { line: 'The impossible has a way of becoming possible.', src: '— Reed Richards' },
      { line: 'The world needs us.', src: '— Susan Storm' },
      { line: 'To the stars and beyond.', src: '— The Fantastic Four' },
    ],
    wakandans: [
      { line: 'Wakanda Forever!', src: '— T’Challa' },
      { line: 'In times of crisis, the wise build bridges, while the foolish build barriers.', src: '— T’Challa' },
      { line: 'Yibambe!', src: '— Okoye' },
      { line: 'Just because something works doesn’t mean it can’t be improved.', src: '— Shuri' },
      { line: 'The world is changing. Whether we like it or not.', src: '— T’Challa' },
    ],
    newavengers: [
      { line: 'We’re the Avengers. We can handle this.', src: '— Doctor Strange' },
      { line: 'Dormammu, I’ve come to bargain.', src: '— Doctor Strange' },
      { line: 'I have nothing to prove to you.', src: '— Carol Danvers' },
      { line: 'I demand a new path.', src: '— America Chavez' },
      { line: 'The future is unwritten.', src: '— Kang the Conqueror' },
    ],
    villain: [
      { line: 'Doom… does not kneel.', src: '— Victor von Doom' },
      { line: 'I am inevitable.', src: '— Thanos' },
      { line: 'The end is coming.', src: '— Victor von Doom' },
      { line: 'You could not live with your own failure. And where did that bring you? Back to me.', src: '— Thanos' },
      { line: 'All hope abandon, ye who enter here.', src: '— Victor von Doom' },
    ],
  };
  // Set by initQuotes(); the faction chooser calls it to switch pools mid-page.
  let syncQuotePool = null;

  // === UTILS ===
  const $ = sel => document.querySelector(sel);
  const $$ = sel => [...document.querySelectorAll(sel)];
  const esc = t => (t+'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  // === COUNTDOWN ===
  function updateCountdown() {
    const now = new Date();
    const diff = RELEASE_DATE - now;
    if (diff <= 0) {
      // Release state
      $('.countdown').innerHTML = `<div class="countdown-segment"><div class="num">DOOMSDAY</div><div class="label">HAS ARRIVED</div></div>`;
      document.body.classList.add('release-day');
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor(diff / 60000);
    const fridays = Math.floor((RELEASE_DATE - new Date(RELEASE_DATE.getFullYear(),0,1)) / (7*86400000));

    // Dynamic milestones
    const milestones = [100, 50, 30, 14, 7, 3, 1];
    milestones.forEach(m => {
      if (d === m) document.body.classList.add(`milestone-${m}`);
    });

    const segs = [
      {num: d, label: 'Days'},
      {num: h, label: 'Hours'},
      {num: m, label: 'Min'},
      {num: s, label: 'Sec'}
    ];
    $('.countdown').innerHTML = segs.map(s =>
      `<div class="countdown-segment"><div class="num">${String(s.num).padStart(2,'0')}</div><div class="label">${s.label}</div></div>`
    ).join('');
  }

  // === COMMAND PALETTE ===
  function initCmdPalette() {
    const cmd = $('#cmd-palette');
    if (!cmd) return;
    const input = $('#cmd-input');

    document.addEventListener('keydown', e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        cmd.classList.add('open');
        input.focus();
      }
      if (e.key === 'Escape') cmd.classList.remove('open');
    });

    input.addEventListener('input', e => {
      const q = e.target.value.toLowerCase().trim();
      const results = $('.cmd-results');
      if (!q) { results.innerHTML = ''; return; }

      // Simple search — replace with full cast manifest later
      const items = [
        {label: 'Characters', hint: 'Browse all cast'},
        {label: 'Watch Guide', hint: 'Prepare for Doomsday'},
        {label: 'Timeline', hint: 'MCU chronology'},
        {label: 'Doom Mode', hint: 'Enter the void'},
        {label: 'Trailer', hint: 'Watch official trailer'},
        {label: 'Stats', hint: 'Cast statistics'}
      ].filter(i => i.label.toLowerCase().includes(q));

      results.innerHTML = items.map(i =>
        `<div class="cmd-item" data-href="/explore/${i.label.toLowerCase().replace(' ','-')}.html">
          <span class="label">${i.label}</span><span class="hint">${i.hint}</span></div>`
      ).join('') || '<div class="cmd-item"><span class="hint">No results</span></div>';
    });

    cmd.addEventListener('click', e => {
      if (e.target === cmd) cmd.classList.remove('open');
    });

    $('.cmd-results').addEventListener('click', e => {
      const item = e.target.closest('.cmd-item');
      if (item && item.dataset.href) {
        window.location.href = item.dataset.href;
      }
    });
  }

  // === FACTION CHOOSER ===
  const FACTION_SLUGS = {
    'Avengers': 'avengers',
    'X-Men': 'xmen',
    'Fantastic Four': 'fantastic',
    'Wakandans': 'wakandans',
    'New Avengers': 'newavengers',
    'Villain': 'villain'
  };
  function factionSlug(name) {
    return FACTION_SLUGS[name] ||
           String(name).toLowerCase().replace(/[^a-z0-9]+/g, '');
  }
  function initFactionChooser() {
    // Crossfade the hero backdrop when the side changes (homepage only).
    function crossfadeHeroBg() {
      const bg = document.querySelector('.hero-bg');
      if (!bg || bg.dataset.fading) return;
      bg.dataset.fading = '1';
      bg.style.transition = 'opacity 0.45s ease';
      bg.style.opacity = '0';
      setTimeout(() => {
        // Clear the inline backgroundImage so the CSS cascade (body.faction-*)
        // can deliver the new faction's image. Without this, getComputedStyle
        // returns the stale inline value from the previous switch.
        bg.style.backgroundImage = '';
        const img = getComputedStyle(bg).backgroundImage;
        if (img && img !== 'none') bg.style.backgroundImage = img;
        void bg.offsetWidth;                  // force reflow so the fade animates
        bg.style.opacity = '';
        setTimeout(() => { delete bg.dataset.fading; }, 620);
      }, 420);
    }

    // Apply a side to <body> (faction-<slug>) and light up its button.
    function applyFaction(label) {
      const slug = factionSlug(label);
      [...document.body.classList].forEach(c => {
        if (c.indexOf('faction-') === 0) document.body.classList.remove(c);
      });
      if (slug) document.body.classList.add(`faction-${slug}`);
      $$('.faction-btn').forEach(b =>
        b.classList.toggle('on', b.dataset.faction === label));
      crossfadeHeroBg();
      if (syncQuotePool) syncQuotePool();
      if (window.doomsdayAudio) window.doomsdayAudio.playStinger(slug);
      if (window.updateFactionPoll) window.updateFactionPoll(label);
      if (window.glitchIncursionGauge) window.glitchIncursionGauge();
    }

    $$('.faction-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const faction = btn.dataset.faction;
        localStorage.setItem('doomsday-faction', faction);
        applyFaction(faction);
      });
    });

    // Restore saved faction
    const saved = localStorage.getItem('doomsday-faction');
    if (saved) applyFaction(saved);
  }

  // === CAST MANIFEST + PREV/NEXT ===
  // Character order comes from cast-manifest.json (alphabetical by slug, i.e.
  // actor). Neighbors are rendered by name so "Previous / Next" always says
  // where it goes, and the current spot is shown in the middle.
  async function initCastNav() {
    const slug = document.body.dataset.slug;
    if (!slug) return;

    try {
      const resp = await fetch('../assets/js/cast-manifest.json');
      const cast = await resp.json();
      const idx = cast.findIndex(c => c.slug === slug);
      if (idx === -1) return;

      const prev = cast[idx - 1];
      const next = cast[idx + 1];
      const shortName = n => {
        // "Sam Wilson / Captain America" -> "Sam Wilson" — keep it compact.
        const primary = (n || '').split('/')[0].trim();
        return primary || n || '';
      };

      if (prev) {
        $('#prev-link').href = `${prev.slug}.html`;
        $('#prev-link').setAttribute('aria-label', `Previous: ${prev.name}`);
        $('#prev-link').innerHTML = `← ${esc(shortName(prev.name))}`;
      } else {
        $('#prev-link').style.visibility = 'hidden';
      }

      if (next) {
        $('#next-link').href = `${next.slug}.html`;
        $('#next-link').setAttribute('aria-label', `Next: ${next.name}`);
        $('#next-link').innerHTML = `${esc(shortName(next.name))} →`;
      } else {
        $('#next-link').style.visibility = 'hidden';
      }

      const mark = $('#char-pos');
      if (mark) mark.textContent = `${idx + 1} of ${cast.length}`;
    } catch (e) {
      console.warn('Cast manifest not loaded');
    }
  }

  // === DOOM MODE (Easter Egg) ===
  let doomClicks = 0;
  function initDoomEasterEgg() {
    // Konami code
    const konami = 'ArrowUpArrowUpArrowDownArrowDownArrowLeftArrowRightArrowLeftArrowRightba';
    let konamiIdx = 0;
    document.addEventListener('keydown', e => {
      if (e.key === konami[konamiIdx]) {
        konamiIdx++;
        if (konamiIdx === konami.length) {
          enterDoomMode();
          konamiIdx = 0;
        }
      } else {
        konamiIdx = 0;
      }
    });

    // Click Doom logo 5 times
    const brand = $('.brand');
    if (brand) {
      brand.addEventListener('click', () => {
        doomClicks++;
        if (doomClicks >= 5) {
          enterDoomMode();
          doomClicks = 0;
        }
      });
    }

    // Idle takeover (60s)
    let idleTimer;
    const resetIdle = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        if (Math.random() < 0.1) enterDoomMode(); // 10% chance after idle
      }, 60000);
    };
    document.addEventListener('mousemove', resetIdle);
    document.addEventListener('keydown', resetIdle);
  }

  function enterDoomMode() {
    document.body.classList.add('doom-mode');
    // Brief glitch effect
    document.body.style.transition = 'filter 0.1s';
    setTimeout(() => {
      document.body.style.filter = 'hue-rotate(-30deg)';
      setTimeout(() => {
        document.body.style.filter = '';
        document.body.style.transition = '';
      }, 500);
    }, 100);
  }

  // === POST-CREDIT SCENE ===
  function initPostCredit() {
    if (!document.querySelector('.post-credit')) return;
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        $('.post-credit').classList.add('visible');
      }
    }, {threshold: 0.1});

    const foot = $('footer');
    if (foot) observer.observe(foot);
  }

  // === NAV HIDE ON SCROLL ===
  let lastScroll = 0;
  function initNavScroll() {
    window.addEventListener('scroll', () => {
      const curr = window.scrollY;
      const nav = $('.nav');
      if (curr > lastScroll && curr > 100) {
        nav.classList.add('hidden');
        nav.classList.remove('open'); // close the mobile dropdown if it slides away
      } else {
        nav.classList.remove('hidden');
      }
      lastScroll = curr;
    }, {passive: true});
  }

  // === MOBILE NAV (hamburger + per-page mini logos) ===
  // The toggle and the page icons are injected here so every page generator
  // (build_explore / build_mcu / build.py / static index.html) stays byte-identical.
  const NAV_ICONS = {
    'home': '<path d="M3 11l9-8 9 8"/><path d="M5 9.5V20h14V9.5"/><path d="M10 20v-6h4v6"/>',
    'characters': '<circle cx="12" cy="8" r="4"/><path d="M5 20c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5"/>',
    'eye of agamotto': '<circle cx="12" cy="12" r="3"/><path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6z"/>',
    'universes': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a12.5 12.5 0 0 1 0 18 12.5 12.5 0 0 1 0-18z"/>',
    'watch guide': '<circle cx="12" cy="12" r="9"/><path d="M9.8 8.6v6.8l6-3.4z"/>',
    'timeline': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.4 2"/>',
    'stats': '<path d="M5 20v-8M12 20V5M19 20v-9"/>',
    'memorial': '<path d="M12 21s7-4.1 7-10V5.6L12 3 5 5.6V11c0 5.9 7 10 7 10z"/>',
    'trailer': '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M7 4v16M17 4v16M3 9h4M3 14h4M17 9h4M17 14h4"/>',
    'explore': '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-1.9 5.1-5.1 1.9 1.9-5.1z"/>'
  };
  function pageIcon(label) {
    const inner = NAV_ICONS[(label || '').trim().toLowerCase()] ||
      '<circle cx="12" cy="12" r="3.2"/>';
    return '<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      inner + '</svg>';
  }

  function initMobileNav() {
    const nav = $('.nav');
    const inner = $('.nav-inner');
    if (!nav || !inner) return;

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-toggle';
    btn.setAttribute('aria-label', 'Toggle navigation');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', 'nav-menu');
    btn.innerHTML = '<span></span><span></span><span></span>';
    inner.insertBefore(btn, inner.firstChild);

    const menu = nav.querySelector('ul');
    if (menu) {
      menu.id = 'nav-menu';
      [...menu.querySelectorAll('li a')].forEach(a => {
        a.insertAdjacentHTML('afterbegin', pageIcon(a.textContent));
      });
    }

    const setOpen = (open) => {
      nav.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', String(open));
    };

    btn.addEventListener('click', e => {
      e.stopPropagation();
      setOpen(!nav.classList.contains('open'));
    });

    if (menu) menu.addEventListener('click', () => setOpen(false));

    document.addEventListener('click', e => {
      if (nav.classList.contains('open') && !nav.contains(e.target)) setOpen(false);
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && nav.classList.contains('open')) setOpen(false);
    });
  }

  // === REDUCED MOTION ===
  function initReducedMotion() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.body.classList.add('reduce-motion');
    }
  }

  // === CINEMATIC STARTUP LOADER ===
  // Only runs on pages that carry the #loader overlay (the homepage).
  function initLoader() {
    const loader = $('#loader');
    if (!loader) return;

    const bar = $('#loader-bar');
    const status = $('#loader-status');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.body.classList.add('loading');
    document.body.classList.add('reduce-motion-loader');

    // Subtle rising particles (skipped for reduced motion).
    const particles = $('#loader-particles');
    if (particles && !reduced) {
      const COUNT = 18;
      for (let i = 0; i < COUNT; i++) {
        const p = document.createElement('span');
        p.className = 'particle';
        p.style.left = (Math.random() * 100).toFixed(1) + '%';
        p.style.animationDuration = (4 + Math.random() * 5).toFixed(2) + 's';
        p.style.animationDelay = (Math.random() * 4).toFixed(2) + 's';
        particles.appendChild(p);
      }
    }

    // Status beat tied to progress, so the label tracks the bar.
    const phases = [
      [0,  'ESTABLISHING SIGNAL'],
      [25, 'SYNCING TIMELINE'],
      [48, 'LOADING MULTIVERSE'],
      [68, 'CALIBRATING DOOM'],
      [90, 'ARCHIVE READY']
    ];
    const total = reduced ? 250 : 1650;  // keep the intro short
    const stepMs = 50;
    const inc = 100 / (total / stepMs);
    let progress = 0;
    let beat = 0;

    const tick = setInterval(() => {
      progress = Math.min(100, progress + inc);
      if (bar) bar.style.width = progress + '%';
      if (status) {
        while (beat + 1 < phases.length && progress >= phases[beat + 1][0]) beat++;
        status.innerHTML = phases[beat][1] + ' <span class="pct">' + Math.round(progress) + '%</span>';
      }
      if (progress >= 100) finish();
    }, stepMs);

    // Fail-safe so the loader can never hang the page.
    const failSafe = setTimeout(finish, reduced ? 700 : 2400);

    function finish() {
      clearInterval(tick);
      clearTimeout(failSafe);
      loader.classList.add('done');
      document.body.classList.remove('loading');
      setTimeout(() => loader.remove(), 800);
    }
  }

  // === YOUTUBE TRAILER ===
  // Autoplays muted on load (static iframe already carries autoplay+mute as a
  // no-JS fallback) and exposes an unmute toggle via the IFrame API.
  function initTrailer() {
    const shell = $('#trailer-frame');
    if (!shell) return;

    const holder = document.createElement('div');
    holder.id = 'trailer-player';
    shell.appendChild(holder);

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'trailer-toggle';
    btn.setAttribute('aria-label', 'Unmute trailer');
    btn.innerHTML = '<span class="ico">🔇</span><span class="lbl">Tap for sound</span>';
    btn.disabled = true;
    shell.appendChild(btn);

    let player = null;

    function paint(muted) {
      btn.innerHTML = muted
        ? '<span class="ico">🔇</span><span class="lbl">Tap for sound</span>'
        : '<span class="ico">🔊</span><span class="lbl">Mute</span>';
      btn.setAttribute('aria-label', muted ? 'Unmute trailer' : 'Mute trailer');
    }

    function boot() {
      if (!window.YT || !window.YT.Player || player) return;
      const fallback = shell.querySelector('iframe');
      if (fallback) fallback.style.display = 'none';

      player = new YT.Player(holder, {
        videoId: 'irVNGjRFZGk',
        width: '100%',
        height: '100%',
        playerVars: { autoplay: 1, mute: 1, playsinline: 1, rel: 0, controls: 1 },
        events: {
          onReady: () => {
            player.setVolume(70);
            paint(true);
            btn.disabled = false;
            player.playVideo();
          }
        }
      });

      btn.addEventListener('click', () => {
        if (!player) return;
        const willUnmute = player.isMuted();
        if (willUnmute) player.unMute(); else player.mute();
        paint(!willUnmute);
      });
    }

    if (window.YT && window.YT.Player) boot();
    else {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
      window.onYouTubeIframeAPIReady = boot;
    }
  }

  // === ACCORDIONS ===
  // Native <details> already toggles; this only smooths the open/close and
  // makes sure reduced-motion users get an instant snap.
  function initAccordions() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return; // <details> toggles natively; no animation needed
    $$('details.acc').forEach(d => {
      const body = d.querySelector('.acc-body, .mv-body, .r-body');
      d.addEventListener('toggle', () => {
        if (!body) return;
        if (d.open) {
          body.style.maxHeight = 'none';
        }
      });
    });
  }

  // === TIMELINE TRACKER ===
  // The rail's sticky dot (CSS: .tl-track top:40vh) rides the viewport with
  // the user's scroll. JS finds whichever card's vertical center is nearest
  // that 40vh landing line and zooms it (the "ball landed here" highlight).
  function initTimelineTracker() {
    const track = $('.tl-track');
    if (!track) return; // this page has no timeline rail
    const items = $$('.tl-item');
    if (!items.length) return;

    function update() {
      const viewH = window.innerHeight;
      const landingY = viewH * 0.4; // matches .tl-track { top: 40vh }
      let best = null, bestDist = Infinity;
      items.forEach(it => {
        const r = it.getBoundingClientRect();
        const d = Math.abs((r.top + r.height / 2) - landingY);
        if (d < bestDist) { bestDist = d; best = it; }
      });
      items.forEach(it => it.classList.toggle('zoom', it === best));
    }

    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { ticking = false; update(); });
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    update();
  }

  function initQuotes() {
    const line = $('.quote-line');
    const src = $('.quote-src');
    if (!line || !src) return; // homepage only

    const poolForBody = () => {
      const cls = [...document.body.classList].find(c => c.indexOf('faction-') === 0);
      const slug = cls ? cls.slice('faction-'.length) : '';
      return QUOTE_POOLS[slug] || QUOTE_POOLS.default;
    };

    let pool = poolForBody();
    let i = 0;

    const show = idx => {
      const q = pool[idx % pool.length];
      line.classList.add('fade-out');
      src.classList.add('fade-out');
      setTimeout(() => {
        line.textContent = `“${q.line}”`;
        src.textContent = q.src;
        line.classList.remove('fade-out');
        src.classList.remove('fade-out');
      }, 420);
    };

    const step = () => { i += 1; show(i); };

    // Re-select the pool when the theme changes (called from applyFaction).
    syncQuotePool = () => {
      pool = poolForBody();
      i = 0;
      show(i);
    };

    show(0);
    setInterval(step, 5000);
  }

  // === SMOOTH PAGE TRANSITIONS (entire site) ===
  function initPageTransitions() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Soft fade-in on every page load.
    if (!reduced) document.body.classList.add('page-enter');

    // Veil that fades in while the next page loads.
    let veil = $('#page-veil');
    if (!veil) {
      veil = document.createElement('div');
      veil.id = 'page-veil';
      document.body.appendChild(veil);
    }
    if (reduced) return;

    document.addEventListener('click', e => {
      // cmd-palette results and nav links are <a>; buttons are handled elsewhere.
      const a = e.target.closest('a');
      if (!a) return;
      if (a.target && a.target !== '_self') return;          // _blank / _top…
      if (a.hasAttribute('download')) return;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') ||
          href.startsWith('mailto:') || href.startsWith('tel:')) return;
      let url;
      try { url = new URL(a.href, location.href); }
      catch { return; }
      if (url.origin !== location.origin) return;            // external only
      e.preventDefault();
      if (document.startViewTransition) {
        document.startViewTransition(() => {
          window.location.href = url.href;
        });
      } else {
        veil.classList.add('on');
        setTimeout(() => { window.location.href = url.href; }, 340);
      }
    });
  }

  // === SCROLL REVEAL ANIMATIONS ===
  function initScrollReveal() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return; // CSS handles instant reveal

    // Collect every card / section / heading that should rise into view.
    // Using selector-based discovery keeps build scripts untouched.
    const candidates = $$(
      '.mem-card, .stat-card, .cast-card, .card, ' +
      '.wrap > section, .explore-grid .card, .cat-card, ' +
      '.stat-grid .stat-card, .mem-grid .mem-card'
    );
    // De-duplicate (sections also match .wrap > section which may overlap)
    const seen = new Set();
    const targets = candidates.filter(el => {
      if (seen.has(el)) return false;
      seen.add(el);
      // Already handled by the catalogue stagger — skip
      if (el.classList.contains('js-animate')) return false;
      // The timeline rail has its own scroll-zoom affordance. Exclude it (and
      // the section wrapping it) so its cards are never parked at opacity:0 —
      // otherwise a long rail can stay invisible if the observer mis-fires.
      if (el.classList.contains('tl-item') || el.querySelector('.tl-rail')) return false;
      el.classList.add('reveal');
      return true;
    });
    if (!targets.length) return;

    let observer;
    try {
      observer = new IntersectionObserver((entries) => {
        entries.forEach(en => {
          if (en.isIntersecting) {
            en.target.classList.add('revealed');
            observer.unobserve(en.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });
    } catch {
      // No IntersectionObserver (or init failure): never leave content hidden.
      targets.forEach(el => el.classList.add('revealed'));
      return;
    }
    targets.forEach(el => observer.observe(el));
  }

  // === HOLLYWOOD CINEMATIC AUDIO SUITE ===
  function initAudioEngine() {
    let ctx = null;
    let enabled = localStorage.getItem('doomsday_audio_v1') === 'on';
    let ambientAudio = null;
    let synthDroneOsc1 = null;
    let synthDroneOsc2 = null;
    let synthDroneGain = null;

    // Detect asset path prefix based on pathname depth
    const isDeep = window.location.pathname.includes('/explore/');
    const isCatDeep = window.location.pathname.includes('/catalogue/');
    const prefix = isCatDeep ? '../../' : (isDeep ? '../' : '');

    const getCtx = () => {
      if (!ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) ctx = new AudioCtx();
      }
      if (ctx && ctx.state === 'suspended') {
        ctx.resume();
      }
      return ctx;
    };

    // Deep cinematic dampened mechanical click (replaces arcade blip)
    const playClick = () => {
      if (!enabled) return;
      try {
        const c = getCtx();
        if (!c) return;
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(140, c.currentTime);
        osc.frequency.exponentialRampToValueAtTime(35, c.currentTime + 0.04);
        gain.gain.setValueAtTime(0.08, c.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.04);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start();
        osc.stop(c.currentTime + 0.04);
      } catch (err) {}
    };

    // Low-frequency tactile confirmation
    const playCheck = () => {
      if (!enabled) return;
      try {
        const c = getCtx();
        if (!c) return;
        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(90, c.currentTime);
        osc.frequency.setValueAtTime(120, c.currentTime + 0.06);
        gain.gain.setValueAtTime(0.09, c.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + 0.18);
        osc.connect(gain);
        gain.connect(c.destination);
        osc.start();
        osc.stop(c.currentTime + 0.18);
      } catch (err) {}
    };

    // Massive Hollywood Movie Trailer Sub-Bass Hit / Braam
    const playTrailerImpact = () => {
      if (!enabled) return;
      // Try playing MP3 asset first
      try {
        const sfx = new Audio(`${prefix}assets/audio/cinematic-impact.mp3`);
        sfx.volume = 0.65;
        const playPromise = sfx.play();
        if (playPromise !== undefined) {
          playPromise.catch(() => {
            // Fallback to high-end Web Audio sub-bass braam
            synthesizeBraam();
          });
        }
      } catch (e) {
        synthesizeBraam();
      }
    };

    const synthesizeBraam = () => {
      try {
        const c = getCtx();
        if (!c) return;
        const t = c.currentTime;
        
        // Primary sub-bass oscillator
        const subOsc = c.createOscillator();
        const subGain = c.createGain();
        subOsc.type = 'sine';
        subOsc.frequency.setValueAtTime(65, t);
        subOsc.frequency.exponentialRampToValueAtTime(28, t + 0.85);

        subGain.gain.setValueAtTime(0.35, t);
        subGain.gain.exponentialRampToValueAtTime(0.001, t + 0.95);
        subOsc.connect(subGain);
        subGain.connect(c.destination);
        subOsc.start(t);
        subOsc.stop(t + 0.95);

        // Low brass overtone with filter
        const brassOsc = c.createOscillator();
        const brassFilter = c.createBiquadFilter();
        const brassGain = c.createGain();

        brassOsc.type = 'sawtooth';
        brassOsc.frequency.setValueAtTime(55, t);
        brassOsc.frequency.exponentialRampToValueAtTime(45, t + 0.7);

        brassFilter.type = 'lowpass';
        brassFilter.frequency.setValueAtTime(160, t);
        brassFilter.frequency.exponentialRampToValueAtTime(40, t + 0.8);

        brassGain.gain.setValueAtTime(0.18, t);
        brassGain.gain.exponentialRampToValueAtTime(0.001, t + 0.85);

        brassOsc.connect(brassFilter);
        brassFilter.connect(brassGain);
        brassGain.connect(c.destination);
        brassOsc.start(t);
        brassOsc.stop(t + 0.85);
      } catch (err) {}
    };

    // Background Ambient Score (Direct Loop without slow fade delay)
    const TARGET_VOLUME = 0.35;

    const startAmbientTheme = () => {
      if (!ambientAudio) {
        ambientAudio = new Audio(`${prefix}assets/audio/ambient-theme.mp3`);
        ambientAudio.loop = true;
        ambientAudio.volume = TARGET_VOLUME;
      }

      ambientAudio.volume = TARGET_VOLUME;
      ambientAudio.play().catch(() => {
        // Fallback to atmospheric dark orchestral drone
        startSynthDrone();
      });
    };

    const stopAmbientTheme = () => {
      if (ambientAudio) {
        ambientAudio.pause();
        ambientAudio.currentTime = 0;
      }
      stopSynthDrone();
    };

    const startSynthDrone = () => {
      try {
        const c = getCtx();
        if (!c || synthDroneGain) return;
        const t = c.currentTime;

        synthDroneGain = c.createGain();
        synthDroneGain.gain.setValueAtTime(0.001, t);
        synthDroneGain.gain.linearRampToValueAtTime(0.08, t + 2.5);

        const filter = c.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(95, t);

        synthDroneOsc1 = c.createOscillator();
        synthDroneOsc1.type = 'triangle';
        synthDroneOsc1.frequency.setValueAtTime(55, t); // A1 note

        synthDroneOsc2 = c.createOscillator();
        synthDroneOsc2.type = 'sine';
        synthDroneOsc2.frequency.setValueAtTime(55.4, t); // Detuned for slow beat

        synthDroneOsc1.connect(filter);
        synthDroneOsc2.connect(filter);
        filter.connect(synthDroneGain);
        synthDroneGain.connect(c.destination);

        synthDroneOsc1.start();
        synthDroneOsc2.start();
      } catch (err) {}
    };

    const stopSynthDrone = () => {
      try {
        if (synthDroneGain && ctx) {
          const t = ctx.currentTime;
          synthDroneGain.gain.linearRampToValueAtTime(0.001, t + 0.8);
          setTimeout(() => {
            if (synthDroneOsc1) { synthDroneOsc1.stop(); synthDroneOsc1 = null; }
            if (synthDroneOsc2) { synthDroneOsc2.stop(); synthDroneOsc2 = null; }
            synthDroneGain = null;
          }, 850);
        }
      } catch (err) {}
    };

    window.doomsdayAudio = {
      playClick,
      playCheck,
      playTrailerImpact,
      startAmbientTheme,
      stopAmbientTheme
    };
    window.playTrailerImpact = playTrailerImpact;
    window.playSfx = (type) => {
      if (type === 'check') playCheck();
      else if (type === 'impact') playTrailerImpact();
      else playClick();
    };

    const toggle = $('#audio-toggle');
    const updateBtn = () => {
      if (!toggle) return;
      const icon = toggle.querySelector('#audio-icon') || toggle;
      const label = toggle.querySelector('#audio-label');
      toggle.classList.toggle('active', enabled);
      if (enabled) {
        if (icon) icon.textContent = '🔊';
        if (label) label.textContent = 'SOUND ON';
      } else {
        if (icon) icon.textContent = '🔇';
        if (label) label.textContent = 'SOUND OFF';
      }
    };
    updateBtn();

    if (toggle) {
      toggle.addEventListener('click', () => {
        enabled = !enabled;
        localStorage.setItem('doomsday_audio_v1', enabled ? 'on' : 'off');
        updateBtn();
        if (enabled) {
          getCtx();
          playClick();
          startAmbientTheme();
        } else {
          stopAmbientTheme();
        }
      });
    }

    document.addEventListener('click', e => {
      if (e.target.closest('.faction-btn, .btn, .pill, #share-btn, #add-calendar, .preset-card, .deck-slot')) {
        playClick();
      }
    });
  }

  // === INCURSION THREAT GAUGE ===
  function initIncursionGauge() {
    const wrap = $('#incursion-gauge-wrap');
    const numEl = $('#incursion-num');
    const barEl = $('#incursion-bar-fill');
    const statusEl = $('#incursion-status');
    if (!wrap) return;

    const ANCHOR_START = new Date('2024-07-26T18:00:00-07:00').getTime();
    const TARGET = RELEASE_DATE.getTime();

    function updateGauge() {
      const now = Date.now();
      const totalSpan = TARGET - ANCHOR_START;
      const elapsed = now - ANCHOR_START;
      const rawPct = Math.min(99.9, Math.max(10.0, (elapsed / totalSpan) * 100));
      const displayPct = rawPct.toFixed(1) + '%';

      if (numEl) numEl.textContent = displayPct;
      if (barEl) barEl.style.width = displayPct;

      if (statusEl) {
        if (rawPct > 90) {
          statusEl.textContent = 'INCURSION VECTOR: CRITICAL • PHASE VI COLLAPSE IMMINENT';
          statusEl.style.color = '#ff4d6d';
        } else if (rawPct > 70) {
          statusEl.textContent = 'UNIVERSAL CONVERGENCE DETECTED • EARTH-616 & EARTH-828 PROXIMITY';
          statusEl.style.color = 'var(--accent)';
        } else {
          statusEl.textContent = 'TIMELINE TELEMETRY ACTIVE • MONITORING INBOUND INCURSION';
        }
      }
    }

    updateGauge();

    window.glitchIncursionGauge = () => {
      wrap.style.boxShadow = '0 0 35px var(--glow), inset 0 0 25px rgba(var(--accent-rgb), 0.3)';
      setTimeout(() => {
        wrap.style.boxShadow = '';
      }, 450);
    };
  }

  // === INTERACTIVE WATCHLIST TRACKER ===
  function initWatchlistTracker() {
    const card = $('#wl-progress-card');
    const checkboxes = $$('.wl-checkbox');
    if (!card && !checkboxes.length) return;

    const STORAGE_KEY = 'doomsday_watchlist_v1';
    let watchedSet = new Set();
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      if (Array.isArray(saved)) watchedSet = new Set(saved);
    } catch (e) {}

    const counterNum = $('#wl-counter-num');
    const counterPct = $('#wl-counter-pct');
    const barFill = $('#wl-bar-fill');
    const statusLabel = $('#wl-status-label');
    const miniCounter = $('#wl-mini-counter');
    const miniBarFill = $('#wl-mini-bar-fill');
    const collapseBtn = $('#wl-collapse-btn');
    const expandBtn = $('#wl-expand-btn');

    const COLLAPSE_KEY = 'doomsday_wl_collapsed';
    if (card && localStorage.getItem(COLLAPSE_KEY) === 'true') {
      card.classList.add('collapsed');
    }

    const toggleCollapse = () => {
      if (!card) return;
      const isCollapsed = card.classList.toggle('collapsed');
      localStorage.setItem(COLLAPSE_KEY, isCollapsed ? 'true' : 'false');
      if (window.doomsdayAudio) window.doomsdayAudio.playClick();
    };

    if (collapseBtn) collapseBtn.addEventListener('click', toggleCollapse);
    if (expandBtn) expandBtn.addEventListener('click', toggleCollapse);

    function syncUI() {
      const total = checkboxes.length;
      let count = 0;

      checkboxes.forEach(cb => {
        const id = cb.dataset.watchId;
        const isWatched = watchedSet.has(id);
        cb.checked = isWatched;
        const item = cb.closest('li');
        if (item) item.classList.toggle('wl-item-watched', isWatched);
        if (isWatched) count++;
      });

      const pct = total > 0 ? Math.round((count / total) * 100) : 0;
      if (counterNum) counterNum.textContent = `${count} / ${total}`;
      if (counterPct) counterPct.textContent = `${pct}% Complete`;
      if (barFill) barFill.style.width = `${pct}%`;
      if (miniCounter) miniCounter.textContent = `${count} / ${total} • ${pct}%`;
      if (miniBarFill) miniBarFill.style.width = `${pct}%`;

      if (statusLabel) {
        if (count === 0) statusLabel.textContent = 'Ready to begin your marathon';
        else if (pct < 25) statusLabel.textContent = 'Timeline training underway';
        else if (pct < 50) statusLabel.textContent = 'Approaching Multiverse collision';
        else if (pct < 75) statusLabel.textContent = 'Battleworld clearance approved';
        else if (pct < 100) statusLabel.textContent = 'Almost ready for Doomsday';
        else statusLabel.textContent = '🏆 100% PREPARED FOR DOOMSDAY!';
      }
    }

    checkboxes.forEach(cb => {
      cb.addEventListener('change', () => {
        const id = cb.dataset.watchId;
        if (cb.checked) {
          watchedSet.add(id);
          if (window.doomsdayAudio) window.doomsdayAudio.playCheck();
        } else {
          watchedSet.delete(id);
          if (window.doomsdayAudio) window.doomsdayAudio.playClick();
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify([...watchedSet]));
        syncUI();
      });
    });

    const btnEssential = $('#wl-check-essential');
    if (btnEssential) {
      btnEssential.addEventListener('click', () => {
        checkboxes.forEach(cb => {
          if (cb.dataset.isEssential === 'true') {
            watchedSet.add(cb.dataset.watchId);
          }
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify([...watchedSet]));
        if (window.doomsdayAudio) window.doomsdayAudio.playCheck();
        syncUI();
      });
    }

    const btnClear = $('#wl-clear-all');
    if (btnClear) {
      btnClear.addEventListener('click', () => {
        if (!confirm('Reset your watchlist progress?')) return;
        watchedSet.clear();
        localStorage.removeItem(STORAGE_KEY);
        if (window.doomsdayAudio) window.doomsdayAudio.playClick();
        syncUI();
      });
    }

    syncUI();
  }

  // === FACTION WAR STANDINGS ===
  function initFactionPoll() {
    const container = $('#fs-list');
    if (!container) return;

    const baseWeights = {
      'Villain': { name: 'Doctor Doom', class: 'villain', votes: 1420 },
      'Avengers': { name: 'Avengers', class: 'avengers', votes: 1050 },
      'Fantastic Four': { name: 'Fantastic Four', class: 'fantastic', votes: 610 },
      'X-Men': { name: 'X-Men', class: 'xmen', votes: 480 },
      'Wakandans': { name: 'Wakandans', class: 'wakandans', votes: 240 },
      'New Avengers': { name: 'New Avengers', class: 'newavengers', votes: 160 }
    };

    function renderStandings(userFaction) {
      const tally = { ...baseWeights };
      if (userFaction && tally[userFaction]) {
        tally[userFaction].votes += 60;
      }

      const totalVotes = Object.values(tally).reduce((acc, f) => acc + f.votes, 0);
      const sorted = Object.entries(tally).sort((a, b) => b[1].votes - a[1].votes);

      container.innerHTML = sorted.map(([key, data]) => {
        const pct = Math.round((data.votes / totalVotes) * 100);
        const isMine = userFaction === key;
        return `
          <div class="fs-item">
            <div class="fs-meta">
              <span class="fs-name">${data.name} ${isMine ? '<span class="badge" style="font-size:0.65rem;padding:0.1rem 0.4rem;">YOUR ALLEGIANCE</span>' : ''}</span>
              <span class="fs-pct">${pct}%</span>
            </div>
            <div class="fs-track">
              <div class="fs-fill ${data.class}" style="width: ${pct}%"></div>
            </div>
          </div>
        `;
      }).join('');

      const totalEl = $('#fs-total');
      if (totalEl) totalEl.textContent = `${totalVotes.toLocaleString()} multiversal votes logged`;
    }

    const currentSaved = localStorage.getItem('doomsday-faction') || 'Villain';
    renderStandings(currentSaved);

    window.updateFactionPoll = (chosen) => {
      renderStandings(chosen);
    };
  }

  // === MULTIVERSE VERSUS ARENA ===
  async function initVersusArena() {
    const sel1 = $('#vs-char-1');
    const sel2 = $('#vs-char-2');
    const stage = $('#vs-stage');
    if (!sel1 || !sel2 || !stage) return;

    let catalogue = [];
    try {
      const resp = await fetch('../data/catalogue.json');
      catalogue = await resp.json();
    } catch (e) {
      try {
        const resp = await fetch('data/catalogue.json');
        catalogue = await resp.json();
      } catch (err) {}
    }

    if (!catalogue.length) return;

    const sorted = [...catalogue].sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    const optionsHtml = sorted.map(c =>
      `<option value="${c.id}">${esc(c.name)} (${esc(c.alias || c.continuity || 'Marvel')})</option>`
    ).join('');

    sel1.innerHTML = optionsHtml;
    sel2.innerHTML = optionsHtml;

    const doom = sorted.find(c => c.id === 'doctor-doom') || sorted[0];
    const rival = sorted.find(c => c.id === 'iron-man-tony-stark') || sorted[1] || sorted[0];

    sel1.value = doom.id;
    sel2.value = rival.id;

    function renderMatchup() {
      const c1 = catalogue.find(c => c.id === sel1.value) || sorted[0];
      const c2 = catalogue.find(c => c.id === sel2.value) || sorted[1];

      const getEmblem = (c) => {
        if (c.image_url && c.image_verified) {
          return `<img src="${esc(c.image_url)}" alt="${esc(c.name)}">`;
        }
        return `<img src="../assets/img/cat-${esc(c.id)}.svg" alt="${esc(c.name)}" onerror="this.src='../../assets/img/cat-${esc(c.id)}.svg'">`;
      };

      let verdict = 'MUTUAL MULTIVERSE COLLAPSE';
      let analysis = 'Two titans of equal multiversal magnitude. The battle would crack reality itself.';
      if (c1.id === 'doctor-doom') {
        verdict = 'DOCTOR DOOM ADVANTAGE';
        analysis = 'Victor von Doom commands both mastery of sorcery and peak cosmic science. Few survive his gaze.';
      } else if (c2.id === 'doctor-doom') {
        verdict = 'DOCTOR DOOM ADVANTAGE';
        analysis = 'Von Doom’s intellect and armor make him nearly insurmountable in a battle of attrition.';
      } else if (c1.continuity === c2.continuity) {
        verdict = 'INTRA-UNIVERSE DUEL';
        analysis = `Both fighters hail from ${c1.continuity}. Intimate knowledge of each other’s tactics guarantees an intense stalemate.`;
      } else {
        verdict = 'INCURSION ANOMALY';
        analysis = `A cross-reality clash: ${c1.name} of ${c1.continuity} faces ${c2.name} of ${c2.continuity}. Unpredictable multiversal fallout!`;
      }

      stage.innerHTML = `
        <div class="vs-fighter-card">
          <div class="vs-emblem">${getEmblem(c1)}</div>
          <div class="vs-name">${esc(c1.name)}</div>
          <div class="vs-alias">${esc(c1.alias || '—')}</div>
          <div class="vs-stat-pill">${esc(c1.continuity || 'MCU')} • ${esc(c1.status || 'Active')}</div>
          <a class="btn btn-secondary btn-sm" href="catalogue/${esc(c1.id)}.html" style="margin-top:0.35rem;">Dossier &rarr;</a>
        </div>
        <div class="vs-verdict">
          <div class="vs-verdict-title">${verdict}</div>
          <div class="vs-verdict-sub">${analysis}</div>
        </div>
        <div class="vs-fighter-card">
          <div class="vs-emblem">${getEmblem(c2)}</div>
          <div class="vs-name">${esc(c2.name)}</div>
          <div class="vs-alias">${esc(c2.alias || '—')}</div>
          <div class="vs-stat-pill">${esc(c2.continuity || 'MCU')} • ${esc(c2.status || 'Active')}</div>
          <a class="btn btn-secondary btn-sm" href="catalogue/${esc(c2.id)}.html" style="margin-top:0.35rem;">Dossier &rarr;</a>
        </div>
      `;
    }

    sel1.addEventListener('change', () => {
      if (window.doomsdayAudio) window.doomsdayAudio.playClick();
      renderMatchup();
    });
    sel2.addEventListener('change', () => {
      if (window.doomsdayAudio) window.doomsdayAudio.playClick();
      renderMatchup();
    });

    renderMatchup();
  }

  // === DENSITY VIEW SWITCHER (Characters Page) ===
  function initDensityControls() {
    const group = $('#density-group');
    const grid = $('#cat-grid');
    if (!group || !grid) return;

    const STORAGE_KEY = 'doomsday_density_v1';
    const saved = localStorage.getItem(STORAGE_KEY) || 'standard';

    function setDensity(mode) {
      grid.classList.remove('density-dense', 'density-comfortable');
      if (mode === 'dense') grid.classList.add('density-dense');
      if (mode === 'comfortable') grid.classList.add('density-comfortable');

      $$('.density-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.density === mode);
      });
      localStorage.setItem(STORAGE_KEY, mode);
    }

    setDensity(saved);

    group.addEventListener('click', e => {
      const btn = e.target.closest('.density-btn');
      if (!btn) return;
      const mode = btn.dataset.density;
      if (window.doomsdayAudio) window.doomsdayAudio.playClick();
      setDensity(mode);
    });
  }

  // === INIT ===
  document.addEventListener('DOMContentLoaded', () => {
    initLoader();
    initQuotes();
    if ($('.countdown')) updateCountdown(), setInterval(updateCountdown, 1000);
    initCmdPalette();
    initFactionChooser();
    initCastNav();
    initDoomEasterEgg();
    initPostCredit();
    initNavScroll();
    initMobileNav();
    initReducedMotion();
    initPageTransitions();
    initTrailer();
    initAccordions();
    initTimelineTracker();
    initScrollReveal();

    // New interactive features
    initAudioEngine();
    initIncursionGauge();
    initWatchlistTracker();
    initFactionPoll();
    initVersusArena();
    initDensityControls();

    // PWA Service Worker
    if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
      const swPath = (location.pathname.includes('/explore/') || location.pathname.includes('/pages/')) ? '../sw.js' : 'sw.js';
      navigator.serviceWorker.register(swPath).catch(() => {});
    }
  });

})();