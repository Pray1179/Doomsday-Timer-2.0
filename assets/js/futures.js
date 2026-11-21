/**
 * Avengers: Doomsday — 14,000,605 Futures Simulator Engine
 * Client-side procedural multiversal battle simulation.
 * Tailored, randomized narrative generation for any assembled strike team against Victor von Doom.
 */
(function() {
  'use strict';

  // State
  let roster = [];
  let presets = [];
  let selectedChampions = [];

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
  const resultFatalBadge = document.getElementById('result-fatal-badge');
  const resultFatalNarrative = document.getElementById('result-fatal-narrative');
  const resultVictoryNarrative = document.getElementById('result-victory-narrative');
  const resultDivergenceText = document.getElementById('result-divergence-text');

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
            <span class="slot-tag">${champ.continuity}</span>
          </div>
        `;
      } else {
        slot.className = 'deck-slot empty';
        slot.innerHTML = `<span class="slot-plus">+</span><span>Slot ${i + 1} (Empty)</span>`;
      }
      teamDeck.appendChild(slot);
    }

    const count = selectedChampions.length;
    teamCount.textContent = count;

    if (count > 0) {
      simBtn.disabled = false;
      simBtn.querySelector('.sim-btn-text').textContent = `SIMULATE 14,000,605 FUTURES (${count}/5 CHAMPIONS)`;
      simHint.textContent = `Strike team ready. Press above to peer through the Eye of Agamotto across all timeline branches.`;
    } else {
      simBtn.disabled = true;
      simBtn.querySelector('.sim-btn-text').textContent = 'SELECT AT LEAST 1 CHAMPION';
      simHint.textContent = 'Add champions above to unlock the Time Stone calculation.';
    }
  }

  // Add Champion to Team
  function addChampion(champ) {
    if (selectedChampions.length >= 5) {
      alert('Strike Team full! Maximum 5 champions allowed.');
      return;
    }
    if (selectedChampions.some(c => c.id === champ.id)) {
      return;
    }
    selectedChampions.push(champ);
    renderTeamDeck();
    searchInput.value = '';
    searchDropdown.style.display = 'none';
    if (window.playSfx) window.playSfx('click');
  }

  // Remove Champion
  function removeChampion(index) {
    selectedChampions.splice(index, 1);
    renderTeamDeck();
    if (window.playSfx) window.playSfx('click');
  }

  // Autocomplete search
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

  // =========================================================================
  // RICH PROCEDURAL NARRATIVE GENERATION ENGINE (CHARACTERS & POWER ARCHETYPES)
  // =========================================================================

  const CHARACTER_PROFILES = {
    'doctor-strange': {
      attack: 'weaving the Crimson Bands of Cyttorak and fracturing mirror dimensions across the throne room',
      support: 'projecting Tao Mandalas to shield the strike team from Latverian eldritch radiation',
      divergence: 'cast the Images of Ikonn in reverse phase, blinding Doom\'s astral sensors',
      threat: '<strong>Anti-Vishanti Sigil Array:</strong> Doom weaves Chthonian null-hexes into his armor, transforming Strange\'s mirror dimensions into localized crushing vacuums.'
    },
    'wolverine-2024': {
      attack: 'lunging with berserker fury, adamantium claws aimed directly at Doom\'s chest reactor',
      support: 'soaking lethal plasma fire with his accelerated cellular healing factor to open a vanguard lane',
      divergence: 'delay the claw strike by exactly 0.7 seconds until Doom\'s thermal exhaust vents',
      threat: '<strong>Magnetic Inversion Solenoid:</strong> Doom polarizes the ambient magnetic field, locking Logan\'s adamantium skeleton in mid-air while cryogenic traps trigger.'
    },
    'spider-man-peter-parker': {
      attack: 'launching high-velocity web-slings, swinging across the crumbling citadel pillars',
      support: 'pulling teammates out of Doom\'s disintegration beams at the speed of precognition',
      divergence: 'web-sling the secondary regulator valve instead of targeting Doom\'s faceplate',
      threat: '<strong>Infrasonic Resonance Grid:</strong> Doom floods the chamber with 180dB sensory-overload pulses, scrambling spider-sense and disintegrating web fluids.'
    },
    'thor': {
      attack: 'summoning a world-splitting barrage of Asgardian lightning and kinetic hammer strikes',
      support: 'channeling atmospheric storm winds to deflect Doom\'s orbital particle lances',
      divergence: 'hurl Stormbreaker into the leyline grounding rod rather than Doom\'s armor',
      threat: '<strong>Divine Lightning Siphons:</strong> Latverian absorption conduits divert Asgardian thunder directly into Doom\'s reality battery, supercharging his shields.'
    },
    'iron-man-tony-stark': {
      attack: 'unleashing an unibeam salvo backed by micro-missile kinetic swarms',
      support: 'jamming Latverian targeting telemetry and hacking Doombot command protocols',
      divergence: 'redirect all auxiliary arc reactor power into Doom\'s dimensional feedback dampener',
      threat: '<strong>Sub-Atomic Nanite Virus:</strong> Doom injects a microscopic techno-plague that overrides Stark OS in 34 milliseconds, locking repulsors.'
    },
    'deadpool-wade-wilson': {
      attack: 'flinging dual katanas and high-explosive ordnance through sheer fourth-wall lunacy',
      support: 'distracting Doom with unrelenting psychological agitation and immortal meat-shielding',
      divergence: 'throw the live thermite grenade into the primary exhaust hopper at the 3-second mark',
      threat: '<strong>Chrono-Stasis Decapitation:</strong> Doom locks Wade Wilson in a micro-timeloop where cellular matter is annihilated faster than regeneration can ignite.'
    },
    'scarlet-witch-wanda-maximoff': {
      attack: 'warping probability itself and tearing through Doom\'s reality shields with raw Chaos Magic',
      support: 'anchoring the squad\'s physical existence against multiversal unraveling',
      divergence: 'collapse the hex sphere inward onto Doom\'s power relays rather than his person',
      threat: '<strong>Chthonic Resonance Siphon:</strong> Doom invokes darkhold dampening sigils, turning Wanda\'s chaos probability hexes back onto the team\'s life-force.'
    },
    'reed-richards': {
      attack: 'stretching across spatial dimensions to manually rewire Doom\'s World Loom consoles',
      support: 'calculating quantum probability angles to guide team strikes into micro-flaws',
      divergence: 'sever the timeline anchor relay with a tachyon scalpel at 99.4% saturation',
      threat: '<strong>Hyper-Spatial Shears:</strong> Driven by personal obsession, Doom deploys tachyon blades designed to dissect unstable-molecule elastic cells across 4 dimensions.'
    },
    'loki': {
      attack: 'weaving thousands of temporal illusory duplicates while manipulating time-slipping currents',
      support: 'rewriting minor narrative vectors to alter Doom\'s spell trajectories',
      divergence: 'anchor the temporal weave into Doom\'s throne base rather than the outer portal',
      threat: '<strong>Narrative Strand Disruptor:</strong> Doom plants chronos-dampener spikes, severing the God of Stories\' temporal threads in raw anti-matter.'
    },
    'captain-america-steve-rogers': {
      attack: 'ricocheting the vibranium shield into Doom\'s optic sensors with pinpoint tactical precision',
      support: 'coordinating battlefield movements and maintaining unbreakable squad morale',
      divergence: 'use the shield to ground the Latverian energy arc rather than deflecting it',
      threat: '<strong>Vibranium Sonic Fracture:</strong> Doom pulses ultrasonic shattering harmonics, neutralizing kinetic absorption and bruising bone through armor.'
    },
    'captain-america-sam-wilson': {
      attack: 'sweeping down in high-velocity vibranium wing dives while deploying redwing telemetry scans',
      support: 'providing aerial tactical reconnaissance and extracting wounded heroes from the kill-zone',
      divergence: 'shear the secondary power conduit with the port wing blade at exactly 00:01:18',
      threat: '<strong>Vortex Disruption Nets:</strong> Latverian atmospheric turrets fire gravimetric suppression webs, dragging aerial combatants into the killing field.'
    },
    'bucky-barnes': {
      attack: 'firing high-caliber armor-piercing rounds while driving his vibranium cybernetic arm into Doom\'s joints',
      support: 'laying heavy suppression fire to prevent Doombot reinforcements from encircling the team',
      divergence: 'detonate the magnetic EMP charge inside the arm socket while locked with Doom\'s gauntlet',
      threat: '<strong>Cybernetic EMP Lock:</strong> Doom triggers a wireless command override that locks Bucky\'s cybernetic servos in rigid stasis.'
    },
    'black-panther-shuri': {
      attack: 'unleashing kinetic absorption bursts from suit-woven vibranium micro-threads and sonic gauntlets',
      support: 'utilizing Wakandan stealth cloaking to disrupt Doom\'s thermal tracking arrays',
      divergence: 'discharge the suit\'s stored kinetic pulse into the floor leyline instead of Doom',
      threat: '<strong>Kinetic Null-Field:</strong> Doom activates an inverted gravity field that drains stored kinetic energy before discharge.'
    },
    'daredevil-matt-murdock': {
      attack: 'striking nerve clusters and acoustic weak points with billy-club acrobatics',
      support: 'sensing micro-vibrations in Doom\'s reality loom to forecast incoming attacks',
      divergence: 'strike the resonant frequency node behind Doom\'s right shoulder blade at 00:01:12',
      threat: '<strong>Acoustic Flash-Bangs:</strong> Automated citadel defense turrets detonate continuous high-frequency sound-bombs, blinding Matt Murdock\'s radar-sense.'
    },
    'blade': {
      attack: 'slashing with etched titanium swords and delivering ultraviolet explosive ordnance',
      support: 'executing lethal tactical decapitations against Doom\'s supernatural thralls',
      divergence: 'drive the silver-alloy blade into the cooling conduit behind the throne',
      threat: '<strong>Ultraviolet Absorption Barrier:</strong> Doom converts UV radiation and occult kinetic energy into a crimson barrier of blood magic.'
    },
    'punisher-frank-castle': {
      attack: 'unloading heavy belt-fed armor-piercing rounds and detonating shaped claymores',
      support: 'funneling Doom\'s cyborg legion into lethal ambush kill-zones',
      divergence: 'fire the final tungsten-core round into the ventilation valve rather than Doom\'s head',
      threat: '<strong>Ballistic Deflection Grid:</strong> Doom\'s personal forcefield deflects all kinetic projectiles back at the shooter at supersonic velocity.'
    },
    'magneto': {
      attack: 'crushing Doom\'s citadel architecture and stripping the armor\'s titanium alloys',
      support: 'erecting an impenetrable electromagnetic dome around the entire squad',
      divergence: 'rip the ferrous iron from the planetary core below rather than Doom\'s armor',
      threat: '<strong>Superconducting Solenoid Core:</strong> Doom generates a localized zero-magnetic void, rendering Erik Lehnsherr unable to manipulate the alloy.'
    },
    'hulk-bruce-banner': {
      attack: 'delivering seismic-shattering haymakers that tear craters through the citadel floor',
      support: 'drawing Doom\'s heaviest energy blasts through sheer indestructible mass',
      divergence: 'smash the foundational tectonic anchor rather than charging Doom directly',
      threat: '<strong>Kinetic Redistribution Plating:</strong> Doom\'s promethium-infused breastplate absorbs 100% of blunt force, converting gamma rage into radial plasma blasts.'
    },
    'captain-marvel-carol-danvers': {
      attack: 'blasting binary photon beams capable of burning through planetary crusts',
      support: 'intercepting and disintegrating orbital bombardment strikes from Doom\'s fleet',
      divergence: 'channel photon reserves into the leyline battery to induce a reverse overload',
      threat: '<strong>Photon Drain Grid:</strong> Citadel spires act as light-gathering prisms, draining Carol Danvers\' photon reserves to accelerate the reality incursion.'
    },
    'victor-von-doom': {
      attack: 'unleashing matching Latverian sorcery and cosmic technology against his alternate self',
      support: 'predicting every move of God Emperor Doom through identical strategic arrogance',
      divergence: 'concede intellectual inferiority for exactly 1.4 seconds to breach his variant\'s guard',
      threat: '<strong>Paradoxical Mirror Lockdown:</strong> God Emperor Doom deploys the Prime Sovereign Directive, locking the variant Doom in an existential reality tether.'
    }
  };

  // Archetype dynamic profile generator for any other Marvel character
  function getProfile(c) {
    if (CHARACTER_PROFILES[c.id]) {
      return CHARACTER_PROFILES[c.id];
    }

    const tags = (c.tags || []).map(t => t.toLowerCase());
    const name = (c.name || '').toLowerCase();
    const cont = (c.continuity || '').toLowerCase();

    const isMagic = tags.includes('magic') || tags.includes('sorcerer') || /strange|wong|clea|ancient|agatha|billy|witch/i.test(name);
    const isMutant = tags.includes('mutant') || tags.includes('x-men') || cont.includes('x-men') || /cyclops|storm|jean|gambit|colossus|nightcrawler|beast|rogue|mystique|laura|x-23|sabretooth/i.test(name);
    const isCosmic = tags.includes('cosmic') || tags.includes('god') || tags.includes('alien') || /surfer|warlock|sersi|nova|marvel|adam|asgardian/i.test(name);
    const isTech = tags.includes('tech') || tags.includes('genius') || tags.includes('armor') || /shuri|pym|ant-man|wasp|rocket|war machine|vision/i.test(name);
    const isBruiser = tags.includes('strength') || tags.includes('tank') || /thing|juggernaut|colossus|drax|abomination|red guardian/i.test(name);
    const isAgile = tags.includes('spider') || /parker|morales|venom|spider/i.test(name);

    if (isMagic) {
      return {
        attack: `channeling ancient mystical incantations and binding runes against Doom's astral perimeter`,
        support: `erecting eldritch forcefields to absorb Doom's dark magical fallout`,
        divergence: `whisper the sealing hex backwards into the leyline conduit at 00:01:20`,
        threat: `<strong>Astral Ward Nullification:</strong> Doom counters ${c.name}'s mystic arts by siphoning eldritch leylines directly into his throne batteries.`
      };
    }
    if (isMutant) {
      return {
        attack: `unleashing mutant genetic mastery in an overwhelming localized offensive`,
        support: `flanking Doom's vanguard to prevent mutant suppression clamps from deploying`,
        divergence: `redirect the mutant energy discharge into the primary exhaust vent rather than Doom's armor`,
        threat: `<strong>Sentinel-Derived Genetic Dampener:</strong> Doom deploys micro-collars that emit neuro-frequencies, temporarily suppressing ${c.name}'s X-gene.`
      };
    }
    if (isCosmic) {
      return {
        attack: `channeling raw cosmic stellar energy into Doom's outer planetary forcefield`,
        support: `neutralizing incoming orbital kinetic bombardment strikes`,
        divergence: `vent cosmic reserves into the reality anchor rather than sustaining the shield`,
        threat: `<strong>Cosmic Energy Converter:</strong> Doom's siphon towers absorb ${c.name}'s cosmic output, converting divine radiation into Battleworld containment barriers.`
      };
    }
    if (isTech) {
      return {
        attack: `overloading Latverian defense firewalls with counter-intrusion quantum viruses`,
        support: `providing tactical frequency sweeps and jamming Doombot telemetry`,
        divergence: `detonate the secondary battery inside the regulator housing at exactly 00:00:44`,
        threat: `<strong>Techno-Organic EMP Wave:</strong> Doom pulses high-frequency magnetic waves that fry ${c.name}'s tech schematics and weapon relays.`
      };
    }
    if (isBruiser) {
      return {
        attack: `shattering the citadel floor with titanic kinetic strikes, forcing Doom off balance`,
        support: `absorbing Doom's primary repulsor beams with sheer physical invulnerability`,
        divergence: `tackle Doom into the secondary grounding conduit rather than the primary throne`,
        threat: `<strong>Kinetic Conversion Armor:</strong> Doom's promethium-titanium weave converts ${c.name}'s blunt impact into searing omnidirectional plasma.`
      };
    }
    if (isAgile) {
      return {
        attack: `executing rapid acrobatic flanking strikes across the crumbling superstructure`,
        support: `extracting teammates from targeted orbital kill-zones with split-second reflexes`,
        divergence: `feint toward the left pillar, baiting Doom's blast into the cooling array`,
        threat: `<strong>Acoustic Spatial Denial:</strong> Latverian sonic traps detonate at ultrasonic frequencies, denying ${c.name} close-quarters leverage.`
      };
    }

    // Default soldier / martial / spy / legacy
    return {
      attack: `delivering surgical combat strikes and coordinated tactical suppression fire`,
      support: `holding the perimeter against Doombot swarms and coordinating squad movements`,
      divergence: `fire the final ordnance into the throne's lower heat baffle at exactly 00:01:05`,
      threat: `<strong>Automated Flechette Array:</strong> Citadel turrets saturate the ground with 10,000 vibranium micro-darts, denying ${c.name} tactical footing.`
    };
  }

  // Pick random item from array
  function pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  // Procedural Generator for Squad Outcomes
  function generateSquadOutcome(squad) {
    const lead = squad[0];
    const second = squad[1] || squad[0];
    const third = squad[2] || squad[1] || squad[0];

    const pLead = getProfile(lead);
    const pSecond = getProfile(second);
    const pThird = getProfile(third);

    // Build Threat Matrix (3-4 tailored entries)
    const threatItems = [];
    squad.forEach(c => {
      const p = getProfile(c);
      if (p.threat && !threatItems.includes(p.threat)) {
        threatItems.push(`<div>${p.threat}</div>`);
      }
    });
    // Add universal Doom dominance threat if fewer than 3
    if (threatItems.length < 3) {
      threatItems.push(`<div><strong>God Emperor Sovereignty:</strong> Victor von Doom commands both supreme mastery of sorcery and peak cosmic science. His throne siphons reality itself.</div>`);
    }

    // Dynamic Timeline Variation Numbers
    const nearMissTimelineNum = pickRandom([
      '14,000,604',
      '13,998,412',
      '14,000,599',
      '13,874,205',
      '14,000,601',
      '13,999,998'
    ]);

    // Tragic Near-Victory Narrative Arcs
    const fatalTemplates = [
      `Vanguard ${lead.name} breaches the outer bastions of Doomstadt, ${pLead.attack}. ${second.name} coordinates tactical flanking, ${pSecond.support}. Pushed into the inner sanctum, Doom's titanium mask cracks under the onslaught. Victory is within reach—until Doom smiles. A subterranean antimatter pulse triggers beneath the floorplates. The squad is consumed in a blinding temporal feedback loop as Doom resets the local reality. Outcome: Absolute chronological erasure.`,

      `${second.name} navigates the subterranean conduits while ${lead.name} draws God Emperor Doom's undivided fury in the upper court, ${pLead.attack}. At the critical juncture, the squad forces Doom onto one knee. ${second.name} severs the primary multiversal leyline, collapsing Doom's shields to zero. But Doom rigged the leyline as a dead-man's switch: without siphon restraint, the multiversal incursion collapses instantly onto the battlefield, crushing the entire sector in an inescapable dimensional sinkhole.`,

      `Executing an audacious perimeter trap, the strike team encircles God Emperor Doom. ${lead.name} coordinates an overwhelming assault, ${pLead.attack}, while ${second.name} provides critical suppression, ${pSecond.support}. Doom appears contained within a folded pocket dimension for 3 minutes and 42 seconds. But Victor von Doom whispers an ancient incantation from the Darkhold, inverting the dimensional geometry. The folded pocket implodes, turning the heroes' own kinetic energy into a lethal shockwave.`,

      `After an exhausting 40-minute war of attrition across the shattered ruins of Battleworld, ${lead.name} and ${second.name} corner Victor von Doom at the World Loom. ${lead.name} delivers a seemingly fatal blow, ${pLead.attack}. The tyrant's armor disintegrates into slag. But as the squad lowers their guard, the smoldering shell dissolves into celestial nanites—it was an astral Doombot proxy. The true God Emperor Doom descends from the tear in the sky, unleashing the full cosmic fury of the Beyonders.`,

      `${lead.name} leads a relentless frontal assault, ${pLead.attack}. Backed by ${second.name}'s tactical cover, ${pSecond.support}, the team shatters Doom's defensive wards one by one. With Doom's forcefield exhausted, ${lead.name} prepares the execution strike. In the final microsecond, Doom detonates a localized chrono-grenade directly inside his own breastplate. Time dilates backward, freezing the heroes in an eternal stasis field while Doom recharges his cosmic matrix.`,

      `${second.name} makes a desperate distraction run, soaking Doom's particle beams so that ${lead.name} can strike the exposed cooling core. ${lead.name} presses forward, ${pLead.attack}, driving Doom backward into the throne dais. But Doom's armored gauntlet clamps down with godlike grip onto ${lead.name}'s weapon. Whispering 'You fought well, but Doom is inevitable,' he discharges raw siphon energy straight through the conduit, terminating the timeline.`
    ];

    // Sole Victory Confluence Narrative Arcs
    const victoryTemplates = [
      `Rather than attempting to match God Emperor Doom's infinite cosmic power, the squad realizes raw force is fatal. ${second.name} executes an unexpected feint, ${pSecond.support}, forcing Doom to channel 100% of his siphon energy into an omnidirectional eradication wave. In the exact 1.8-second refractory window while Doom's mystic armor exhausts heat, ${lead.name} strikes not at Doom, but at the dimensional grounding capacitor, ${pLead.attack}. The redirected cosmic feedback overloads Doom's suit from within, shattering his divine mantle and restoring the multiverse.`,

      `${lead.name} engages Victor von Doom in a ferocious duel, ${pLead.attack}, purposely taking the brunt of his wrath to hold his gaze. Meanwhile, ${second.name} ignores the duel completely and slips behind the throne dais, ${pSecond.support}. When Doom raises his hand for the fatal execution strike on ${lead.name}, ${third.name} severs the three multiversal anchor pylons simultaneously. Deprived of multiversal life-force, God Emperor Doom's godhood evaporates into harmless embers, freeing the branched realities.`,

      `Drawing upon their distinct dimensional origins across the multiverse, ${lead.name} and ${second.name} strike Doom's barrier not with brute force, but at precise resonant frequencies. ${lead.name} strikes with full power, ${pLead.attack}, while ${second.name} synchronizes, ${pSecond.support}. The harmonic interference pattern creates an existential dissonance within Doom's reality loom. Cracks spread through the citadel's ceiling as the stolen universes reassert their sovereignty. Doom is disarmed, his armor shattered, and the Multiversal War is ended.`,

      `Across 14,000,604 futures, Doom's precognitive sensors anticipate every hero's move. But in this solitary timeline, ${second.name} executes a seemingly irrational sacrifice maneuver, ${pSecond.support}. The sheer illogical nature of the move causes Doom's tactical algorithms to stall for 0.4 seconds. In that microscopic window, ${lead.name} slips past the perimeter wards and ${pLead.attack}, severing the master regulator valve. Battleworld fractures peacefully into restored timelines.`,

      `As God Emperor Doom summons a colliding dying universe to crush the team, ${lead.name} and ${second.name} hold the perimeter against all odds. ${second.name} stabilizes the dimensional threshold, ${pSecond.support}. ${lead.name} channels the incoming cosmic energy directly into Doom's armor heatsinks, ${pLead.attack}. Unable to absorb the infinite weight of two colliding realities, Doom's containment systems rupture. The tyrant collapses, and the sacred leylines are liberated.`,

      `The squad baits Doom into activating his ultimate temporal purge. As the reality loom begins spinning to erase the multiverse, ${lead.name} drives Doom onto the defense, ${pLead.attack}. ${second.name} uses the distraction to plant an inverted chronos crystal into the loom's drive gear. When Doom triggers the erasure wave, the paradox reflects backward into his own psyche. Victor von Doom's stolen omnipotence dissolves, leaving only a broken mortal in the ruins of his throne.`
    ];

    // Critical Divergence Point Templates
    const divergenceTemplates = [
      `T-minus 00:01:14: ${lead.name} must NOT strike Doom's breastplate, but instead feint left, allowing ${second.name} to ${pSecond.divergence}.`,
      `T-minus 00:00:39: ${second.name} must hold fire for exactly 2.4 seconds until Doom's secondary heat baffles reach 100% saturation before severing the conduit.`,
      `T-minus 00:02:08: ${lead.name} must sacrifice their weapon into the Latverian loom gear, opening an 0.8-second window for ${second.name} to breach the throne.`,
      `T-minus 00:00:52: ${lead.name} must ${pLead.divergence}, triggering a recursive paradox within Doom's armor before the reality wave expands.`,
      `T-minus 00:01:47: ${second.name} must resist the tactical instinct to save ${lead.name}, allowing the kinetic shockwave to propel ${lead.name} into the secondary power relay.`,
      `T-minus 00:00:18: ${lead.name} must sever the left dimensional conduit at the exact millisecond Doom's armor visor shifts to emerald resonance.`,
      `T-minus 00:02:35: ${second.name} must ${pSecond.divergence} precisely when Doom reaches the 3rd syllable of his Chthonian invocation.`,
      `T-minus 00:01:05: The squad must cease all offensive fire for 3 consecutive seconds, baiting Doom into stepping onto the unshielded leyline junction.`
    ];

    return {
      odds: "1 IN 14,000,605",
      odds_pct: "0.0000071%",
      timeline_num: nearMissTimelineNum,
      threat_matrix: threatItems,
      fatal_timeline: pickRandom(fatalTemplates),
      victory_timeline: pickRandom(victoryTemplates),
      divergence_point: pickRandom(divergenceTemplates)
    };
  }

  // Render Outcome to Dossier
  function renderOutcome(outcome) {
    resultOdds.textContent = outcome.odds;
    resultOddsPct.textContent = `${outcome.odds_pct} VICTORY PROBABILITY`;

    if (resultFatalBadge && outcome.timeline_num) {
      resultFatalBadge.innerHTML = `TIMELINE #${outcome.timeline_num} &bull; FATAL NEAR-VICTORY`;
    }

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

      // Generate dynamic character-tailored narrative
      const outcome = generateSquadOutcome(selectedChampions);
      renderOutcome(outcome);

      simResults.scrollIntoView({ behavior: 'smooth' });
    });
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
  }

  // Startup
  document.addEventListener('DOMContentLoaded', () => {
    initData();
    renderTeamDeck();
    attachEvents();
  });

})();
