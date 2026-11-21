/**
 * Avengers: Doomsday — 14,000,605 Futures Simulator Engine
 * Client-side battle simulation, team builder, preset loader,
 * and optional NVIDIA NIM / Gemini API streaming integration.
 */
(function() {
  'use strict';

  // State
  let roster = [];
  let presets = [];
  let selectedChampions = [];
  let apiKey = localStorage.getItem('time_stone_api_key') || '';
  let apiProvider = localStorage.getItem('time_stone_provider') || 'nvidia';

  // Elements
  const searchInput = document.getElementById('champ-search-input');
  const searchDropdown = document.getElementById('champ-dropdown');
  const teamDeck = document.getElementById('team-deck');
  const teamCount = document.getElementById('team-count');
  const clearBtn = document.getElementById('clear-team');
  const simBtn = document.getElementById('run-simulation-btn');
  const simHint = document.getElementById('sim-hint');
  const simChamber = document.getElementById('sim-chamber');
  const counterDisplay = document.getElementById('counter-display');
  const simResults = document.getElementById('sim-results');

  // Dossier fields
  const resultOdds = document.getElementById('result-odds');
  const resultOddsPct = document.getElementById('result-odds-pct');
  const resultThreatMatrix = document.getElementById('result-threat-matrix');
  const resultFatalNarrative = document.getElementById('result-fatal-narrative');
  const resultVictoryNarrative = document.getElementById('result-victory-narrative');
  const resultDivergenceText = document.getElementById('result-divergence-text');
  const aiActiveBadge = document.getElementById('ai-active-badge');
  const aiProviderLabel = document.getElementById('ai-provider-label');

  // Modal elements
  const openModalBtn = document.getElementById('open-api-modal');
  const closeModalBtn = document.getElementById('close-api-modal');
  const apiModal = document.getElementById('api-modal');
  const saveKeyBtn = document.getElementById('save-key-btn');
  const clearKeyBtn = document.getElementById('clear-key-btn');
  const aiProviderSelect = document.getElementById('ai-provider-select');
  const aiKeyInput = document.getElementById('ai-key-input');
  const keyIndicator = document.getElementById('key-indicator');
  const keyLabel = document.getElementById('key-label');

  // Init Data
  function initData() {
    try {
      const rEl = document.getElementById('roster-data');
      if (rEl) roster = JSON.parse(rEl.textContent || '[]');
      const pEl = document.getElementById('presets-data');
      if (pEl) presets = JSON.parse(pEl.textContent || '[]');
    } catch (e) {
      console.warn('Failed to parse roster/preset data:', e);
    }
  }

  // Update UI key indicator
  function updateKeyIndicator() {
    if (apiKey) {
      keyIndicator.classList.add('active');
      keyLabel.textContent = apiProvider === 'nvidia' ? 'AI: NVIDIA NIM (Active)' : 'AI: Gemini (Active)';
    } else {
      keyIndicator.classList.remove('active');
      keyLabel.textContent = 'Connect AI Key (Optional)';
    }
  }

  // Render Team Deck slots
  function renderTeamDeck() {
    teamDeck.innerHTML = '';
    for (let i = 0; i < 5; i++) {
      const champ = selectedChampions[i];
      const slot = document.createElement('div');
      if (champ) {
        slot.className = 'deck-slot filled';
        slot.innerHTML = `
          <button class="slot-remove" type="button" data-index="${i}" title="Remove ${champ.name}">&times;</button>
          <div class="slot-portrait">
            <img src="${champ.img}" alt="${champ.name}" onerror="this.src='../assets/img/cat-${champ.id}.svg'">
          </div>
          <div class="slot-meta">
            <div class="slot-name">${champ.name}</div>
            <div class="slot-alias">${champ.alias || champ.unit}</div>
          </div>
        `;
      } else {
        slot.className = 'deck-slot empty';
        slot.innerHTML = `<span class="slot-plus">+</span><span>Slot ${i + 1} (Empty)</span>`;
      }
      teamDeck.appendChild(slot);
    }

    teamCount.textContent = selectedChampions.length;

    if (selectedChampions.length > 0) {
      simBtn.disabled = false;
      simBtn.querySelector('.sim-btn-text').textContent = 'SIMULATE 14,000,605 TIMELINES';
      simHint.textContent = `Strike team of ${selectedChampions.length} champions assembled. Ready for temporal projection.`;
    } else {
      simBtn.disabled = true;
      simBtn.querySelector('.sim-btn-text').textContent = 'SELECT AT LEAST 1 CHAMPION';
      simHint.textContent = 'Add champions above to unlock the Time Stone calculation.';
    }
  }

  // Add Champion
  function addChampion(champ) {
    if (selectedChampions.length >= 5) {
      alert('Strike team capacity reached (maximum 5 champions). Remove one to replace.');
      return;
    }
    if (selectedChampions.some(c => c.id === champ.id)) {
      alert(`${champ.name} is already in the strike team.`);
      return;
    }
    selectedChampions.push(champ);
    renderTeamDeck();
    searchDropdown.style.display = 'none';
    searchInput.value = '';
    // Audio tick
    if (window.playSfx) window.playSfx('click');
  }

  // Remove Champion
  function removeChampion(index) {
    selectedChampions.splice(index, 1);
    renderTeamDeck();
    if (window.playSfx) window.playSfx('click');
  }

  // Search logic
  function handleSearch() {
    const q = (searchInput.value || '').trim().toLowerCase();
    if (!q) {
      searchDropdown.style.display = 'none';
      return;
    }

    const matches = roster.filter(c => {
      const name = (c.name || '').toLowerCase();
      const alias = (c.alias || '').toLowerCase();
      const unit = (c.unit || '').toLowerCase();
      const cont = (c.continuity || '').toLowerCase();
      return name.includes(q) || alias.includes(q) || unit.includes(q) || cont.includes(q);
    }).slice(0, 8);

    if (matches.length === 0) {
      searchDropdown.innerHTML = '<div class="dropdown-item no-match">No matching movie characters found.</div>';
      searchDropdown.style.display = 'block';
      return;
    }

    searchDropdown.innerHTML = '';
    matches.forEach(m => {
      const item = document.createElement('div');
      item.className = 'dropdown-item';
      item.tabIndex = 0;
      const isSelected = selectedChampions.some(c => c.id === m.id);
      item.innerHTML = `
        <div class="dropdown-thumb">
          <img src="${m.img}" alt="${m.name}" onerror="this.src='../assets/img/cat-${m.id}.svg'">
        </div>
        <div class="dropdown-info">
          <strong>${m.name}</strong>
          <span>${m.alias || m.unit} &bull; ${m.continuity}</span>
        </div>
        ${isSelected ? '<span class="dropdown-selected-tag">Selected</span>' : '<span class="dropdown-add-btn">+ Add</span>'}
      `;
      item.addEventListener('click', () => {
        if (!isSelected) addChampion(m);
      });
      searchDropdown.appendChild(item);
    });
    searchDropdown.style.display = 'block';
  }

  // Load Preset
  function loadPreset(presetId) {
    const p = presets.find(x => x.id === presetId);
    if (!p) return;

    selectedChampions = [];
    p.members.forEach(id => {
      const champ = roster.find(r => r.id === id);
      if (champ) selectedChampions.push(champ);
    });

    renderTeamDeck();
    const assemblerEl = document.getElementById('assembler-section');
    if (assemblerEl) {
      assemblerEl.scrollIntoView({ behavior: 'smooth' });
    }
    if (window.playSfx) window.playSfx('click');
  }

  // Cinematic Counter Roll
  function rollCounter(target, duration, callback) {
    const start = performance.now();
    function step(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(eased * target);
      counterDisplay.textContent = current.toLocaleString();
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        counterDisplay.textContent = target.toLocaleString();
        if (callback) callback();
      }
    }
    requestAnimationFrame(step);
  }

  // Check if current squad matches any preset
  function getMatchingPreset() {
    if (selectedChampions.length === 0) return null;
    const currentIds = selectedChampions.map(c => c.id).sort().join(',');
    for (const p of presets) {
      const pIds = p.members.slice().sort().join(',');
      if (currentIds === pIds) return p;
    }
    return null;
  }

  // Procedural Generator for Custom Squads
  function generateCustomOutcome(squad) {
    const names = squad.map(c => c.name).join(', ');
    const count = squad.length;

    // Has magic or cosmic?
    const hasMagic = squad.some(c => (c.tags || []).includes('magic') || /strange|wanda|loki|wong/i.test(c.id));
    const hasCosmic = squad.some(c => /thor|surfer|carol|marvel|adam/i.test(c.id));
    const hasTech = squad.some(c => /stark|iron|richards|pym|shuri/i.test(c.id));

    let threatItems = [];
    if (hasTech) {
      threatItems.push(`<div><strong>Tech Synchronization:</strong> Doom deploys a localized EMP pulse and nanotech siphons to fracture communications.</div>`);
    } else {
      threatItems.push(`<div><strong>Tech Dominance:</strong> Doom's satellite beam and Doombots maintain complete tactical battlefield control.</div>`);
    }

    if (hasMagic) {
      threatItems.push(`<div><strong>Occult Resonance:</strong> Doom is forced to channel Vishanti defensive barriers, burning through his personal life-force leylines.</div>`);
    } else {
      threatItems.push(`<div><strong>Mystic Vulnerability:</strong> Without Sorcery Supreme mastery, the squad struggles to penetrate Doom's astral forcefield.</div>`);
    }

    threatItems.push(`<div><strong>Direct Engagement:</strong> God Emperor Doom anticipates physical strikes; his armor converts kinetic shockwaves into raw plasma bolts.</div>`);

    const leadChamp = squad[0].name;
    const secondChamp = squad[1] ? squad[1].name : squad[0].name;

    const fatal = `Timeline #14,000,604 — ${leadChamp} coordinates an aggressive assault breaching the perimeter of Doom's Citadel. ${secondChamp} provides critical covering fire, momentarily cracking Doom's armor visor. However, Doom detonates an internal temporal stasis mine. The shockwave freezes the squad in a recursive time dilation pocket while Doom recharges his primary reality loom. Outcome: Complete temporal erasure.`;

    const victory = `Timeline #14,000,605 — Rather than targeting Victor von Doom directly, the squad focuses on his dimensional anchor relays. ${secondChamp} executes a coordinated thermal overload, forcing Doom to vent his mystic capacitors. In the exact 2.1-second refractory window, ${leadChamp} severs the multiversal leyline feed. Deprived of multiversal siphon energy, God Emperor Doom's throne collapses, freeing the branched timelines.`;

    const divergence = `T-minus 00:01:38: ${leadChamp} must hold back the final strike and wait until Doom's secondary heat baffles cycle to 100% capacity before severing the conduit.`;

    return {
      odds: "1 in 14,000,605",
      odds_pct: "0.0000071%",
      threat_matrix: threatItems,
      fatal_timeline: fatal,
      victory_timeline: victory,
      divergence_point: divergence
    };
  }

  // Live AI Stream using NVIDIA NIM or Gemini
  async function runAiStream(squad) {
    const names = squad.map(c => `${c.name} (${c.alias || c.unit})`).join(', ');
    const systemPrompt = `You are Doctor Strange peering through the Time Stone across 14,000,605 alternate futures of the Multiversal War against Victor von Doom (Avengers: Doomsday).
Analyze this strike team: ${names}.
Provide an epic, serious, cinematic report with four clear sections:
1) TACTICAL THREAT ANALYSIS: Doom's counters to this specific squad.
2) TIMELINE #14,000,604 (THE TRAGIC NEAR-VICTORY): How they push Doom to the brink before a fatal tactical error.
3) TIMELINE #14,000,605 (THE SOLE VICTORY CONFLUENCE): The exact sequence of sacrifices, timing, and reality breaches needed to overcome God Emperor Doom.
4) CRITICAL DIVERGENCE POINT: The exact microsecond decision that decides victory.
Keep the tone dark, thrilling, grounded in Marvel lore, and worthy of a Russo Brothers cinematic climax.`;

    aiActiveBadge.style.display = 'inline-flex';
    aiProviderLabel.textContent = apiProvider === 'nvidia' 
      ? 'NVIDIA NIM Streaming Inference (Llama 3.1 70B) Active' 
      : 'Google Gemini Streaming Inference Active';

    resultFatalNarrative.innerHTML = '<span class="streaming-text">Connecting to Temporal Archive...</span>';
    resultVictoryNarrative.innerHTML = '<span class="streaming-text">Streaming timeline vectors...</span>';
    resultThreatMatrix.innerHTML = '<div class="streaming-text">Analyzing Doom defensive matrix...</div>';

    try {
      if (apiProvider === 'nvidia') {
        const response = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          },
          body: JSON.stringify({
            model: 'meta/llama-3.1-70b-instruct',
            messages: [{ role: 'user', content: systemPrompt }],
            temperature: 0.7,
            max_tokens: 1024,
            stream: false
          })
        });

        if (!response.ok) {
          throw new Error(`NVIDIA NIM returned HTTP ${response.status}`);
        }
        const data = await response.json();
        const content = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : '';
        renderAiOutput(content);
      } else {
        // Google Gemini
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: systemPrompt }] }]
          })
        });
        if (!response.ok) {
          throw new Error(`Gemini API returned HTTP ${response.status}`);
        }
        const data = await response.json();
        const content = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
        renderAiOutput(content);
      }
    } catch (err) {
      console.error('AI streaming error, falling back to local simulation:', err);
      aiActiveBadge.style.display = 'none';
      alert(`AI API connection notice: ${err.message}. Falling back to high-fidelity built-in temporal archive.`);
      const outcome = generateCustomOutcome(squad);
      renderOutcome(outcome);
    }
  }

  // Parse and display AI output
  function renderAiOutput(text) {
    resultThreatMatrix.innerHTML = `<div><strong>Neural Analysis:</strong> ${text.slice(0, 300).replace(/\n/g, '<br>')}...</div>`;
    resultFatalNarrative.textContent = text.slice(300, 800) || text;
    resultVictoryNarrative.textContent = text.slice(800, 1400) || text;
    resultDivergenceText.textContent = text.slice(1400) || "T-minus 00:01:24: Precision timing required on the secondary reactor siphon.";
  }

  // Render Outcome to Dossier
  function renderOutcome(outcome) {
    aiActiveBadge.style.display = 'none';
    resultOdds.textContent = outcome.odds;
    resultOddsPct.textContent = `${outcome.odds_pct} VICTORY PROBABILITY`;

    if (Array.isArray(outcome.threat_matrix)) {
      resultThreatMatrix.innerHTML = outcome.threat_matrix.join('');
    } else if (typeof outcome.threat_matrix === 'object') {
      resultThreatMatrix.innerHTML = Object.values(outcome.threat_matrix)
        .map(v => `<div>&bull; ${v}</div>`).join('');
    }

    resultFatalNarrative.textContent = outcome.fatal_timeline;
    resultVictoryNarrative.textContent = outcome.victory_timeline;
    resultDivergenceText.textContent = outcome.divergence_point;
  }

  // Run Simulation Handler
  function handleSimulation() {
    if (selectedChampions.length === 0) return;

    // Trigger audio hit
    if (window.playTrailerImpact) {
      window.playTrailerImpact();
    } else if (window.playSfx) {
      window.playSfx('click');
    }

    // Scroll to chamber and display
    simResults.style.display = 'none';
    simChamber.style.display = 'flex';
    simChamber.scrollIntoView({ behavior: 'smooth' });

    // Roll counter
    rollCounter(14000605, 1800, () => {
      simChamber.style.display = 'none';
      simResults.style.display = 'block';

      const preset = getMatchingPreset();
      if (apiKey) {
        runAiStream(selectedChampions);
      } else if (preset) {
        renderOutcome(preset.canonical);
      } else {
        const customOutcome = generateCustomOutcome(selectedChampions);
        renderOutcome(customOutcome);
      }

      simResults.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // Event Listeners
  function attachEvents() {
    // Search input
    searchInput.addEventListener('input', handleSearch);
    searchInput.addEventListener('focus', handleSearch);

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.style.display = 'none';
      }
    });

    // Remove slot click
    teamDeck.addEventListener('click', (e) => {
      const btn = e.target.closest('.slot-remove');
      if (btn) {
        const idx = parseInt(btn.dataset.index, 10);
        removeChampion(idx);
      }
    });

    // Clear team
    clearBtn.addEventListener('click', () => {
      selectedChampions = [];
      renderTeamDeck();
      simResults.style.display = 'none';
      simChamber.style.display = 'none';
      if (window.playSfx) window.playSfx('click');
    });

    // Preset buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        loadPreset(btn.dataset.preset);
      });
    });

    document.querySelectorAll('.preset-card').forEach(card => {
      card.addEventListener('click', () => {
        loadPreset(card.dataset.preset);
      });
    });

    // Simulate button
    simBtn.addEventListener('click', handleSimulation);

    // Modal events
    openModalBtn.addEventListener('click', () => {
      aiKeyInput.value = apiKey;
      aiProviderSelect.value = apiProvider;
      apiModal.style.display = 'flex';
    });

    closeModalBtn.addEventListener('click', () => {
      apiModal.style.display = 'none';
    });

    apiModal.addEventListener('click', (e) => {
      if (e.target === apiModal) apiModal.style.display = 'none';
    });

    saveKeyBtn.addEventListener('click', () => {
      apiKey = (aiKeyInput.value || '').trim();
      apiProvider = aiProviderSelect.value;
      localStorage.setItem('time_stone_api_key', apiKey);
      localStorage.setItem('time_stone_provider', apiProvider);
      updateKeyIndicator();
      apiModal.style.display = 'none';
      alert('Time Stone AI Key configured. Simulations will now generate live AI battle chronologies.');
    });

    clearKeyBtn.addEventListener('click', () => {
      apiKey = '';
      localStorage.removeItem('time_stone_api_key');
      aiKeyInput.value = '';
      updateKeyIndicator();
      apiModal.style.display = 'none';
      alert('Time Stone AI Key removed. The simulator will use built-in canonical timelines.');
    });
  }

  // Startup
  document.addEventListener('DOMContentLoaded', () => {
    initData();
    renderTeamDeck();
    updateKeyIndicator();
    attachEvents();
  });

})();
