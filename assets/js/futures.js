/**
 * Avengers: Doomsday — 14,000,605 Futures Simulator Engine
 * Client-side battle simulation, team builder, preset loader,
 * and multi-provider AI integration with dynamic model discovery.
 */
(function() {
  'use strict';

  // State
  let roster = [];
  let presets = [];
  let selectedChampions = [];
  let apiKey = localStorage.getItem('time_stone_api_key') || '';
  let apiProvider = localStorage.getItem('time_stone_provider') || 'gemini';
  let selectedModel = localStorage.getItem('time_stone_model') || '';

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
  const testKeyBtn = document.getElementById('test-key-btn');
  const testKeyResult = document.getElementById('test-key-result');
  const toggleKeyVisBtn = document.getElementById('toggle-key-visibility');
  const aiProviderSelect = document.getElementById('ai-provider-select');
  const aiKeyInput = document.getElementById('ai-key-input');
  const aiModelSelect = document.getElementById('ai-model-select');
  const fetchModelsBtn = document.getElementById('fetch-models-btn');
  const aiCustomModelInput = document.getElementById('ai-custom-model-input');
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
      const modelLabel = selectedModel ? ` (${selectedModel.replace(/^models\//, '')})` : '';
      const names = {
        gemini: `AI: Gemini${modelLabel}`,
        groq: `AI: Groq Llama${modelLabel}`,
        nvidia: `AI: NVIDIA NIM${modelLabel}`,
        openrouter: `AI: OpenRouter${modelLabel}`
      };
      keyLabel.textContent = names[apiProvider] || 'AI Active';
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
    const leadChamp = squad[0].name;
    const secondChamp = squad[1] ? squad[1].name : squad[0].name;

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

  // Fetch available models from account API
  async function fetchAvailableModels(provider, key) {
    const cleanKey = (key || '').trim();
    if (!cleanKey) {
      testKeyResult.style.display = 'block';
      testKeyResult.style.color = '#e63946';
      testKeyResult.textContent = '❌ Please enter an API key first.';
      return [];
    }

    testKeyResult.style.display = 'block';
    testKeyResult.style.color = '#a3e6b8';
    testKeyResult.textContent = '⏳ Querying available models from API...';

    if (provider === 'gemini') {
      try {
        const endpoints = [
          `https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(cleanKey)}`,
          `https://generativelanguage.googleapis.com/v1/models?key=${encodeURIComponent(cleanKey)}`
        ];
        let models = [];
        let lastErrTxt = '';
        for (const ep of endpoints) {
          try {
            const res = await fetch(ep, {
              headers: { 'x-goog-api-key': cleanKey }
            });
            if (res.ok) {
              const data = await res.json();
              if (data.models && data.models.length > 0) {
                models = data.models;
                break;
              }
            } else {
              const txt = await res.text();
              try {
                const j = JSON.parse(txt);
                lastErrTxt = j?.error?.message || txt;
              } catch(_) {
                lastErrTxt = txt;
              }
            }
          } catch(e) {
            lastErrTxt = e.message;
          }
        }

        if (models.length > 0) {
          aiModelSelect.innerHTML = '<option value="">-- Choose from your account\'s models --</option>';
          const genModels = models.filter(m => (m.supportedGenerationMethods || []).includes('generateContent'));
          const displayList = genModels.length > 0 ? genModels : models;

          displayList.forEach(m => {
            const opt = document.createElement('option');
            const shortName = m.name.replace(/^models\//, '');
            opt.value = shortName;
            opt.textContent = `${m.displayName || shortName} (${shortName})`;
            aiModelSelect.appendChild(opt);
          });

          // Preselect first or saved model
          if (selectedModel) {
            aiModelSelect.value = selectedModel.replace(/^models\//, '');
            aiCustomModelInput.value = selectedModel;
          } else if (displayList[0]) {
            const firstShort = displayList[0].name.replace(/^models\//, '');
            aiModelSelect.value = firstShort;
            aiCustomModelInput.value = firstShort;
          }

          testKeyResult.style.color = '#00cc55';
          testKeyResult.innerHTML = `✅ Successfully detected <strong>${displayList.length} models</strong>! Pick from the dropdown or type your model below.`;
          return displayList;
        } else {
          testKeyResult.style.color = '#f59e0b';
          testKeyResult.innerHTML = `⚠️ Could not auto-list models${lastErrTxt ? ': ' + lastErrTxt.slice(0, 100) : ''}. You can type your model name directly below (e.g. <code>gemini-2.0-flash</code>, <code>gemini-1.5-flash</code>, <code>gemini-4-hydrogen</code>).`;
        }
      } catch (err) {
        testKeyResult.style.color = '#e63946';
        testKeyResult.textContent = `❌ Model query failed: ${err.message}. You can still type your model name manually.`;
      }
    } else if (provider === 'groq') {
      try {
        const res = await fetch('https://api.groq.com/openai/v1/models', {
          headers: { 'Authorization': `Bearer ${cleanKey}` }
        });
        if (res.ok) {
          const data = await res.json();
          aiModelSelect.innerHTML = '<option value="">-- Choose from Groq models --</option>';
          (data.data || []).forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = m.id;
            aiModelSelect.appendChild(opt);
          });
          testKeyResult.style.color = '#00cc55';
          testKeyResult.innerHTML = `✅ Successfully fetched Groq models! Select from the dropdown.`;
        }
      } catch(err) {
        testKeyResult.style.color = '#e63946';
        testKeyResult.textContent = `❌ Groq query error: ${err.message}`;
      }
    } else {
      testKeyResult.style.color = '#a3e6b8';
      testKeyResult.textContent = `Type your model identifier in the custom model field below.`;
    }
    return [];
  }

  // Call Google Gemini API with smart model discovery & dual auth
  async function callGeminiApi(cleanKey, prompt) {
    const payload = JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 1024
      }
    });

    // Check user-specified custom model first
    const userModel = (aiCustomModelInput && aiCustomModelInput.value ? aiCustomModelInput.value.trim() : '')
      || (aiModelSelect && aiModelSelect.value ? aiModelSelect.value.trim() : '')
      || (selectedModel || '').trim();

    // Candidate models in priority order: user's chosen model first!
    const modelCandidates = [];
    if (userModel) {
      modelCandidates.push(userModel);
    }
    // High-availability model fallbacks
    [
      'gemini-2.0-flash',
      'gemini-2.0-flash-exp',
      'gemini-1.5-flash',
      'gemini-1.5-flash-latest',
      'gemini-1.5-pro',
      'gemini-pro'
    ].forEach(m => {
      if (!modelCandidates.includes(m)) modelCandidates.push(m);
    });

    let lastError = null;

    for (const rawModel of modelCandidates) {
      const cleanPath = rawModel.startsWith('models/') ? rawModel : `models/${rawModel}`;
      const endpoints = [
        `https://generativelanguage.googleapis.com/v1beta/${cleanPath}:generateContent`,
        `https://generativelanguage.googleapis.com/v1/${cleanPath}:generateContent`
      ];

      for (const ep of endpoints) {
        try {
          const url = `${ep}?key=${encodeURIComponent(cleanKey)}`;
          const res = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-goog-api-key': cleanKey
            },
            body: payload
          });

          if (res.ok) {
            const data = await res.json();
            return data.candidates?.[0]?.content?.parts?.[0]?.text || '';
          }

          const errText = await res.text();
          let errJson = null;
          try { errJson = JSON.parse(errText); } catch (_) {}
          const errMsg = errJson?.error?.message || errText.slice(0, 140);

          if (res.status === 404) {
            lastError = new Error(`HTTP 404 on ${cleanPath}: ${errMsg}`);
            continue; // Try next endpoint or model
          }

          if (res.status === 400) {
            throw new Error(`Google API Key Invalid: ${errMsg}`);
          }

          throw new Error(`Google HTTP ${res.status}: ${errMsg}`);
        } catch (e) {
          if (e.message && e.message.includes('Invalid')) throw e;
          lastError = e;
        }
      }
    }

    throw lastError || new Error('All Gemini model endpoints returned 404. Please check the model name.');
  }

  // Dispatch AI Model API Call
  async function callModelApi(provider, key, prompt) {
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const cleanKey = (key || '').trim();

    if (!cleanKey) {
      throw new Error('Please enter an API key.');
    }

    if (provider === 'gemini') {
      return await callGeminiApi(cleanKey, prompt);
    }
    else if (provider === 'groq') {
      const model = (aiCustomModelInput && aiCustomModelInput.value ? aiCustomModelInput.value.trim() : '')
        || (aiModelSelect && aiModelSelect.value ? aiModelSelect.value.trim() : '')
        || 'llama-3.3-70b-versatile';

      const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${cleanKey}`
        },
        body: JSON.stringify({
          model: model,
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          max_tokens: 1024
        })
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Groq HTTP ${res.status}: ${errText.slice(0, 150)}`);
      }
      const data = await res.json();
      return data.choices?.[0]?.message?.content || '';
    }
    else if (provider === 'nvidia') {
      const endpoint = isLocalhost ? '/api/nvidia-proxy' : 'https://integrate.api.nvidia.com/v1/chat/completions';
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${cleanKey}`
          },
          body: JSON.stringify({
            model: 'meta/llama-3.1-70b-instruct',
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.7,
            max_tokens: 1024
          })
        });

        if (res.status === 404 && endpoint === '/api/nvidia-proxy') {
          throw new Error("Local NVIDIA proxy not running. Please run 'python3 scripts/serve.py' in your terminal, or select Groq (runs the same Llama 3.1 70B with browser CORS) or Google Gemini!");
        }

        if (!res.ok) {
          const errText = await res.text();
          throw new Error(`NVIDIA NIM HTTP ${res.status}: ${errText.slice(0, 150)}`);
        }
        const data = await res.json();
        return data.choices?.[0]?.message?.content || '';
      } catch (err) {
        if (err.message && err.message.includes('Failed to fetch')) {
          throw new Error("NVIDIA's cloud blocks direct browser CORS. Run 'python3 scripts/serve.py' locally, or switch provider to Groq (same Llama 3.1 70B) or Google Gemini!");
        }
        throw err;
      }
    } 
    else {
      // OpenRouter supports browser CORS
      const model = (aiCustomModelInput && aiCustomModelInput.value ? aiCustomModelInput.value.trim() : '')
        || 'meta-llama/llama-3.1-70b-instruct';

      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${cleanKey}`
        },
        body: JSON.stringify({
          model: model,
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          max_tokens: 1024
        })
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`OpenRouter HTTP ${res.status}: ${errText.slice(0, 150)}`);
      }
      const data = await res.json();
      return data.choices?.[0]?.message?.content || '';
    }
  }

  // Parse structured AI response into sections
  function parseAiResponse(raw) {
    let threatText = '';
    let fatalText = '';
    let victoryText = '';
    let divText = '';

    const lines = raw.split('\n');
    let currentSec = 0;

    for (let line of lines) {
      const lower = line.toLowerCase();
      if (lower.includes('threat analysis') || lower.includes('tactical threat')) {
        currentSec = 1;
        continue;
      } else if (lower.includes('14,000,604') || lower.includes('fatal near-victory') || lower.includes('near-victory')) {
        currentSec = 2;
        continue;
      } else if (lower.includes('14,000,605') || lower.includes('sole victory') || lower.includes('victory path')) {
        currentSec = 3;
        continue;
      } else if (lower.includes('divergence point') || lower.includes('critical divergence')) {
        currentSec = 4;
        continue;
      }

      if (currentSec === 1) threatText += line + '\n';
      else if (currentSec === 2) fatalText += line + '\n';
      else if (currentSec === 3) victoryText += line + '\n';
      else if (currentSec === 4) divText += line + '\n';
    }

    if (!fatalText.trim() && !victoryText.trim()) {
      const half = Math.floor(raw.length / 2);
      fatalText = raw.slice(0, half);
      victoryText = raw.slice(half);
      threatText = "Tactical simulation synthesized by Time Stone AI neural engine.";
      divText = "Critical Divergence Point: Exact temporal synchronization required at primary catalyst conduit.";
    }

    return {
      threat: threatText.trim() || "Multiversal Leyline Siphon: Doom establishes astral supremacy.",
      fatal: fatalText.trim() || raw.slice(0, 500),
      victory: victoryText.trim() || raw.slice(500, 1200),
      divergence: divText.trim() || "T-minus 00:01:24: Strict execution sequence required on Doom's secondary heat baffles."
    };
  }

  // Live AI Stream Execution
  async function runAiStream(squad) {
    const names = squad.map(c => `${c.name} (${c.alias || c.unit})`).join(', ');
    const systemPrompt = `You are Doctor Strange peering through the Eye of Agamotto across 14,000,605 alternate futures of the Multiversal War against Victor von Doom (Avengers: Doomsday).
Analyze this assembled Strike Team: ${names}.
Provide a vivid, serious, cinematic report with four clearly labeled sections:
1) TACTICAL THREAT ANALYSIS: Specific Doom defensive countermeasures and siphon wards against this team's powers.
2) TIMELINE #14,000,604 (THE TRAGIC NEAR-VICTORY): Detailed narrative of how they push Doom to the brink before a fatal trap destroys them.
3) TIMELINE #14,000,605 (THE SOLE VICTORY CONFLUENCE): The exact sequence of moves, sacrifices, and reality breaches needed to overcome God Emperor Doom.
4) CRITICAL DIVERGENCE POINT: The exact microsecond decision that decides victory.
Keep the tone dark, thrilling, grounded in Marvel lore, and worthy of a Russo Brothers cinematic climax.`;

    aiActiveBadge.style.display = 'inline-flex';
    const providerNames = {
      gemini: 'Google Gemini',
      groq: 'Groq (Llama 3.3 70B)',
      nvidia: 'NVIDIA NIM (Llama 3.1 70B)',
      openrouter: 'OpenRouter (Llama 3.1 70B)'
    };
    const modelTag = selectedModel ? ` [${selectedModel.replace(/^models\//, '')}]` : '';
    aiProviderLabel.textContent = `${providerNames[apiProvider] || 'AI Model'}${modelTag} Active`;

    resultOdds.textContent = "1 IN 14,000,605";
    resultOddsPct.textContent = "0.0000071% VICTORY PROBABILITY";
    resultFatalNarrative.innerHTML = '<span class="streaming-text">Connecting to Multiversal Neural Matrix...</span>';
    resultVictoryNarrative.innerHTML = '<span class="streaming-text">Streaming timeline vectors...</span>';
    resultThreatMatrix.innerHTML = '<div class="streaming-text">Analyzing Doom defensive matrix...</div>';
    resultDivergenceText.textContent = "Calculating timeline branch...";

    try {
      const text = await callModelApi(apiProvider, apiKey, systemPrompt);
      const parsed = parseAiResponse(text);

      resultThreatMatrix.innerHTML = `<div><strong>Neural Analysis:</strong> ${parsed.threat.replace(/\n/g, '<br>')}</div>`;
      resultFatalNarrative.textContent = parsed.fatal;
      resultVictoryNarrative.textContent = parsed.victory;
      resultDivergenceText.textContent = parsed.divergence;
    } catch (err) {
      console.error('AI streaming error, falling back to local simulation:', err);
      aiActiveBadge.style.display = 'none';

      let msg = err.message || '';
      alert(`AI API notice: ${msg}\n\nFalling back to high-fidelity built-in temporal archive.`);

      const outcome = generateCustomOutcome(squad);
      renderOutcome(outcome);
    }
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

    if (window.playTrailerImpact) {
      window.playTrailerImpact();
    } else if (window.playSfx) {
      window.playSfx('click');
    }

    simResults.style.display = 'none';
    simChamber.style.display = 'flex';
    simChamber.scrollIntoView({ behavior: 'smooth' });

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

  // Test Key Connection in Modal
  async function testKeyConnection() {
    const key = (aiKeyInput.value || '').trim();
    const provider = aiProviderSelect.value;

    if (!key) {
      testKeyResult.style.display = 'block';
      testKeyResult.style.color = '#e63946';
      testKeyResult.textContent = '❌ Please enter an API key first.';
      return;
    }

    testKeyResult.style.display = 'block';
    testKeyResult.style.color = '#a3e6b8';
    testKeyResult.textContent = '⏳ Testing connection to AI endpoint...';

    try {
      const pingPrompt = "Respond with exactly the single word 'ACTIVE'.";
      const res = await callModelApi(provider, key, pingPrompt);
      const usedModel = (aiCustomModelInput && aiCustomModelInput.value ? aiCustomModelInput.value.trim() : '')
        || (aiModelSelect && aiModelSelect.value ? aiModelSelect.value.trim() : '')
        || selectedModel;

      testKeyResult.style.color = '#00cc55';
      testKeyResult.innerHTML = `✅ <strong>Connected successfully!</strong><br>Model verified: <code>${usedModel || 'default'}</code><br>Response: "${res.trim().slice(0, 40)}"`;
    } catch (err) {
      testKeyResult.style.color = '#e63946';
      testKeyResult.innerHTML = `❌ Connection failed: ${err.message}<br><small>Tip: Try clicking <strong>Fetch Models 🔄</strong> above to load the exact models your key has access to.</small>`;
    }
  }

  // Event Listeners
  function attachEvents() {
    searchInput.addEventListener('input', handleSearch);
    searchInput.addEventListener('focus', handleSearch);

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.style.display = 'none';
      }
    });

    teamDeck.addEventListener('click', (e) => {
      const btn = e.target.closest('.slot-remove');
      if (btn) {
        const idx = parseInt(btn.dataset.index, 10);
        removeChampion(idx);
      }
    });

    clearBtn.addEventListener('click', () => {
      selectedChampions = [];
      renderTeamDeck();
      simResults.style.display = 'none';
      simChamber.style.display = 'none';
      if (window.playSfx) window.playSfx('click');
    });

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

    simBtn.addEventListener('click', handleSimulation);

    // Modal events
    openModalBtn.addEventListener('click', () => {
      aiKeyInput.value = apiKey;
      aiProviderSelect.value = apiProvider;
      aiCustomModelInput.value = selectedModel;
      testKeyResult.style.display = 'none';
      apiModal.style.display = 'flex';
    });

    closeModalBtn.addEventListener('click', () => {
      apiModal.style.display = 'none';
    });

    apiModal.addEventListener('click', (e) => {
      if (e.target === apiModal) apiModal.style.display = 'none';
    });

    if (toggleKeyVisBtn) {
      toggleKeyVisBtn.addEventListener('click', () => {
        aiKeyInput.type = aiKeyInput.type === 'password' ? 'text' : 'password';
      });
    }

    if (aiProviderSelect) {
      aiProviderSelect.addEventListener('change', () => {
        const prov = aiProviderSelect.value;
        if (prov === 'gemini') {
          aiCustomModelInput.placeholder = 'e.g. gemini-2.0-flash, gemini-1.5-flash, gemini-4-hydrogen...';
        } else if (prov === 'groq') {
          aiCustomModelInput.placeholder = 'e.g. llama-3.3-70b-versatile, llama-3.1-8b-instant...';
        } else if (prov === 'nvidia') {
          aiCustomModelInput.placeholder = 'e.g. meta/llama-3.1-70b-instruct...';
        } else {
          aiCustomModelInput.placeholder = 'e.g. meta-llama/llama-3.1-70b-instruct...';
        }
        testKeyResult.style.display = 'none';
      });
    }

    if (fetchModelsBtn) {
      fetchModelsBtn.addEventListener('click', () => {
        fetchAvailableModels(aiProviderSelect.value, aiKeyInput.value);
      });
    }

    if (aiModelSelect) {
      aiModelSelect.addEventListener('change', () => {
        if (aiModelSelect.value) {
          aiCustomModelInput.value = aiModelSelect.value;
        }
      });
    }

    if (testKeyBtn) {
      testKeyBtn.addEventListener('click', testKeyConnection);
    }

    saveKeyBtn.addEventListener('click', () => {
      apiKey = (aiKeyInput.value || '').trim();
      apiProvider = aiProviderSelect.value;
      selectedModel = (aiCustomModelInput.value || aiModelSelect.value || '').trim();

      localStorage.setItem('time_stone_api_key', apiKey);
      localStorage.setItem('time_stone_provider', apiProvider);
      localStorage.setItem('time_stone_model', selectedModel);

      updateKeyIndicator();
      apiModal.style.display = 'none';
      alert(`Time Stone AI configured with ${apiProvider} (${selectedModel || 'auto'}). Simulations will now stream live AI battle reports.`);
    });

    clearKeyBtn.addEventListener('click', () => {
      apiKey = '';
      selectedModel = '';
      localStorage.removeItem('time_stone_api_key');
      localStorage.removeItem('time_stone_model');
      aiKeyInput.value = '';
      aiCustomModelInput.value = '';
      aiModelSelect.innerHTML = '<option value="">-- Click \'Fetch Models\' to load your account\'s models --</option>';
      testKeyResult.style.display = 'none';
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
