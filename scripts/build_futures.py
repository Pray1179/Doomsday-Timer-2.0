#!/usr/bin/env python3
"""Doomsday Fan Hub — 14,000,605 Futures Simulator Generator.

Generates explore/futures.html: The dedicated Multiverse Battle Simulator
inspired by Doctor Strange in Infinity War. Pure stdlib, deterministic.
"""
import json
from pathlib import Path
import build_explore as ex
import catalogue_util as cu

ROOT = Path(__file__).resolve().parent.parent
EXPLORE = ROOT / "explore"
CATALOGUE_PATH = ROOT / "data" / "catalogue.json"

PRESETS = [
    {
        "id": "616-avengers",
        "name": "Earth-616 Core Avengers",
        "badge": "Original Trinity + Magic",
        "icon": "🛡️",
        "members": [
            "captain-america-steve-rogers",
            "iron-man-tony-stark",
            "thor",
            "scarlet-witch-wanda-maximoff",
            "doctor-strange"
        ],
        "tagline": "The founding pillars of Earth's defense reinforced with reality-warping chaos and eldritch sorcery.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "magic_siphon": "HIGH RISK: Doom absorbs Wanda's Chaos Magic into Latverian leylines.",
                "tech_override": "CRITICAL: Doom's technopathy remotely isolates Stark's nanotech relays.",
                "brute_force": "MODERATE: Thor's lightning pierces shields but overcharges Doom's armor."
            },
            "fatal_timeline": "Timeline #14,000,604 — Stark deploys an orbital vibranium dampener around Castle Doom while Thor and Rogers pin the primary Doombot legion. Wanda breaches the throne room and fractures Doom's mystic aegis. However, Doom triggers a localized temporal reversal rune woven into the castle foundation. Time rewinds 47 seconds, allowing Doom to anticipate Wanda's hex trajectory and sever Stark's arc reactor link. Total casualty rate: 100%.",
            "victory_timeline": "Timeline #14,000,605 — Doctor Strange refuses to engage directly in combat. Instead, Strange casts a mirror dimension labyrinth trapping 99% of the Doombot reinforcements. Stark recognizes Doom's armor frequencies and deliberately overloads his own bleeding edge capacitors, sacrificing his flight propulsion to short Doom's siphon gauntlet. In the exact 1.8-second window of power redistribution, Rogers hurls the Vibranium shield into the armor's heatsink, and Wanda detonates the core from within the Astral Plane. Victor von Doom is severed from the multiversal loom.",
            "divergence_point": "T-minus 00:02:14: Strange must allow Stark to make the sacrifice play without intervening, and Rogers must throw the shield at the secondary exhaust port rather than the headpiece."
        }
    },
    {
        "id": "illuminati",
        "name": "Earth-838 Multiversal Illuminati",
        "badge": "Multiversal High Council",
        "icon": "👁️",
        "members": [
            "reed-richards",
            "charles-xavier-xmen",
            "peggy-carter",
            "doctor-strange",
            "blade"
        ],
        "tagline": "The supreme intellects who make the decisions no one else can make.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "psionic_shielding": "EXTREME: Doom's titanium mask is enchanted with anti-telepathic lead runes.",
                "intellectual_clash": "HIGH: Doom counters Reed's dimensional bridge calculations in real-time.",
                "occult_lethality": "EFFECTIVE: Blade's silver-nitrate and darkhold wards bypass physical shields."
            },
            "fatal_timeline": "Timeline #14,000,604 — Professor X attempts an astral projection lockdown inside Doom's mind while Carter coordinates tactical flanking. Doom anticipated this psychic intrusion; he deliberately stores a dormant Cthon demonic consciousness in his frontal lobe. Xavier's mind is shattered upon entry, causing a psionic shockwave that incapacitates Carter and Reed.",
            "victory_timeline": "Timeline #14,000,605 — Reed Richards does not fight to harm Doom; he fights to dismantle Doom's mathematical confidence. Reed feeds false Incursion coordinates into Doom's temporal chronometer. Believing Earth-616 is already collapsing, Doom redirects 90% of his mystic shields toward stabilization. Blade breaches the ventilation core with occult daylight explosives, and Strange executes an eldritch severance severing Doom's link to the Beyonder energies.",
            "divergence_point": "T-minus 00:01:45: Charles Xavier must remain on the astral perimeter strictly as a decoy, allowing Reed to calibrate the false sensor feed unnoticed."
        }
    },
    {
        "id": "fox-xmen",
        "name": "Fox X-Men Strike Alpha",
        "badge": "Omega-Level Firepower",
        "icon": "⚔️",
        "members": [
            "wolverine-logan",
            "magneto-xmen",
            "jean-grey-xmen",
            "cyclops-xmen",
            "storm-xmen"
        ],
        "tagline": "Mutantkind's fiercest warriors united across cinematic history.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "ferrous_manipulation": "ADVANTAGE: Magneto can exert massive kinetic torque on Doom's armor alloys.",
                "phoenix_entropy": "OVERWHELMING: Jean Grey's telekinesis dissolves matter at the molecular tier.",
                "adamantium_lethality": "HIGH: Wolverine's claws can bypass mystic forcefields if physically engaged."
            },
            "fatal_timeline": "Timeline #14,000,604 — Magneto strips the outer titanium shell of Doom's battle-suit. But Doom's armor is merely a containment vessel for cosmic eldritch plasma. Unshackled from his armor, Doom unleashes pure disintegration magic, atomizing Cyclops and turning Wolverine's skeleton into a magnetic prison against Magneto.",
            "victory_timeline": "Timeline #14,000,605 — Storm summons an atmospheric ionic dead-zone, suffocating all electronic circuits within a 5-mile radius. As Doom switches to occult backup leylines, Jean Grey suppresses his conscious spellcasting while Cyclops delivers a sustained optic blast to fracture the chest medallion. Wolverine, propelled by Magneto at hypersonic velocity, pierces Doom's secondary neural regulator.",
            "divergence_point": "T-minus 00:00:58: Magneto must resist crushing the armor inward, and instead propel Logan through the optic blast breach before Doom recharges his runes."
        }
    },
    {
        "id": "fantastic-four",
        "name": "Fantastic Four & Silver Surfer",
        "badge": "Cosmic Ray Matrix",
        "icon": "🌌",
        "members": [
            "reed-richards-ff",
            "sue-storm-ff",
            "johnny-storm-ff",
            "ben-grimm-ff",
            "silver-surfer-ff"
        ],
        "tagline": "The First Family and the Power Cosmic — Victor von Doom's most personal adversaries.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "power_cosmic": "LETHAL: Norrin Radd manipulates the universal energy spectrum directly.",
                "personal_vendetta": "CRITICAL RISK: Doom prioritizes torturing Reed over strategic victory.",
                "forcefield_containment": "SUPERIOR: Sue Storm's psionic shields can contain sub-atomic antimatter."
            },
            "fatal_timeline": "Timeline #14,000,604 — Johnny Storm goes Supernova inside Sue's invisible containment bubble to vaporize Doom's fortress. Doom redirects the thermal energy into the Baxter Building's negative zone portal, creating a catastrophic vortex that consumes New York.",
            "victory_timeline": "Timeline #14,000,605 — Sue Storm projects an invisible micro-forcefield directly inside Doom's respirator mask, cutting off oxygen while Ben Grimm anchors his gauntlets. The Silver Surfer expends a concentrated blast of the Power Cosmic to neutralize Doom's dimensional tether. Reed Richards catches Victor in an unbreakable stasis coil, neutralizing his threat without triggering the dead-man's planetary bomb.",
            "divergence_point": "T-minus 00:03:02: Johnny Storm must refrain from going Supernova and instead act as a thermal distraction to force Doom to vent his heat baffles."
        }
    },
    {
        "id": "spider-verse",
        "name": "Multiversal Spider-Army",
        "badge": "Web of Life & Destiny",
        "icon": "🕷️",
        "members": [
            "spidey-maguire",
            "spidey-garfield",
            "venom-hardy",
            "madame-web",
            "carnage-ssu"
        ],
        "tagline": "Spider-sense networked across the multiverse to anticipate Doom's every move.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "precognition": "ADVANTAGE: Madame Web's prescience maps Doom's attacks 8 seconds prior.",
                "agility_swarm": "HIGH: Three Spider-Men overwhelm Doombot targeting arrays.",
                "symbiote_vulnerability": "HIGH RISK: Doom's sonic cannons and thermal spells incinerate symbiotes."
            },
            "fatal_timeline": "Timeline #14,000,604 — Venom and Carnage charge the front gates while Maguire and Garfield execute acrobatic disarms. Doom deploys an orbital sonic pulse that liquefies the symbiotes and leaves the wall-crawlers exposed to guided plasma strikes.",
            "victory_timeline": "Timeline #14,000,605 — Madame Web coordinates the battle like a grandmaster, feeding exact millisecond vectors to Maguire and Garfield. The Spider-Men web up the thermal exhaust ports rather than attacking Doom directly. As Doom's armor overheats, Venom anchors the heavy blast doors, and Garfield web-yanks the primary power conduit, triggering an internal fail-safe shutdown.",
            "divergence_point": "T-minus 00:01:12: The Spider-Men must completely avoid melee combat with Doom and focus 100% on exhausting his thermal management system."
        }
    },
    {
        "id": "midnight-suns",
        "name": "Midnight Suns Taskforce",
        "badge": "Occult Street Lethality",
        "icon": "🌙",
        "members": [
            "blade",
            "johnny-blaze-gr",
            "ghost-rider-robbie",
            "matt-murdock-daredevil",
            "frank-castle-punisher"
        ],
        "tagline": "Hellfire, cursed bloodlines, and cold tactical brutality striking Doom's black-magic core.",
        "canonical": {
            "odds": "1 in 14,000,605",
            "odds_pct": "0.0000071%",
            "threat_matrix": {
                "penance_stare": "DECISIVE: Doom has committed countless atrocities; Hellfire burns his soul.",
                "magic_inversion": "EFFECTIVE: Ghost Rider's Spirit of Vengeance cannot be siphoned by mortal spells.",
                "tactical_ambush": "SUPERIOR: Punisher and Daredevil exploit blind spots in Doom's satellite surveillance."
            },
            "fatal_timeline": "Timeline #14,000,604 — Johnny Blaze engages Doom in a direct stare-down. Doom invokes the Vishanti Counter-Seal, bouncing the Penance Stare back into Blaze's human psyche, triggering an uncontrolled demonic implosion that consumes the team.",
            "victory_timeline": "Timeline #14,000,605 — Frank Castle creates a coordinated military distraction using thermite charges on Latverian armories. Daredevil guides Blade through the catacombs by tracking the subterranean heartbeat of Doom's mystic siphon. While Robbie Reyes traps Doom inside a hellfire vortex, Johnny Blaze delivers the Penance Stare from the blind spot behind Doom's mystic mirror. Doom's soul is judged by the weight of a dying multiverse.",
            "divergence_point": "T-minus 00:02:30: Murdock must detect the subterranean acoustic resonance of the siphon before Castle's charges detonate, timing the entrance to the exact millisecond."
        }
    }
]


def load_catalogue():
    if not CATALOGUE_PATH.exists():
        return []
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_futures_page():
    records = load_catalogue()
    
    # Extract compact roster for client-side search & display
    compact_roster = []
    for r in records:
        compact_roster.append({
            "id": r["id"],
            "name": r["name"],
            "alias": r.get("alias", ""),
            "unit": r.get("unit", "Multiverse"),
            "continuity": r.get("continuity", "Marvel"),
            "img": r.get("image_url", f"../assets/img/cat-{r['id']}.svg"),
            "tags": r.get("tags", []),
            "status": r.get("status", "Active")
        })

    roster_json = json.dumps(compact_roster, ensure_ascii=False)
    presets_json = json.dumps(PRESETS, ensure_ascii=False)

    preset_cards = []
    for p in PRESETS:
        member_chips = "".join(f'<span class="preset-pill">{cu.esc(m.split("-")[0].capitalize())}</span>' for m in p["members"][:4])
        preset_cards.append(f"""
        <div class="preset-card" data-preset="{p['id']}">
          <div class="preset-head">
            <span class="preset-icon">{p['icon']}</span>
            <div>
              <h4 class="preset-title">{cu.esc(p['name'])}</h4>
              <span class="preset-badge">{cu.esc(p['badge'])}</span>
            </div>
          </div>
          <p class="preset-desc">{cu.esc(p['tagline'])}</p>
          <div class="preset-members">{member_chips}<span class="preset-pill">+1</span></div>
          <button class="btn btn-sm btn-outline preset-btn" data-preset="{p['id']}">Load Strike Team →</button>
        </div>
        """)

    preset_cards_html = "\n".join(preset_cards)

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "14,000,605 Futures Simulator",
        "description": "Doctor Strange's time-inspection matrix against Doctor Doom in Avengers: Doomsday.",
        "applicationCategory": "EntertainmentApplication"
    })

    return (ex.page_head("14,000,605 Futures", "Doctor Strange's Multiverse Battle Simulator against Victor von Doom.",
                         "/explore/futures.html", jsonld)
            + "<body>" + ex.site_nav("futures")
            + f"""
<header class="hero futures-hero">
  <div class="hero-bg-gem" aria-hidden="true"></div>
  <div class="futures-header-top">
    <span class="gem-badge"><span class="gem-spark"></span> EYE OF AGAMOTTO // TEMPORAL ENGINE</span>
    <button id="open-api-modal" class="btn-api-key" type="button" aria-haspopup="dialog" title="Configure NVIDIA NIM or Gemini API Key">
      <span class="key-status-dot" id="key-indicator"></span>
      <span id="key-label">Connect AI Key (Optional)</span>
    </button>
  </div>
  <h1 class="gem-title">14,000,605 Futures</h1>
  <p class="gem-quote">&ldquo;I went forward in time... to view alternate futures. To see all the possible outcomes of the coming conflict.&rdquo; <span class="quote-author">&mdash; Doctor Strange</span></p>
  <p class="lede gem-lede">Assemble an elite Multiversal Strike Team (up to 5 champions) against Victor von Doom. Calculate survival odds, identify critical divergence points, or stream live AI battle reports.</p>
</header>

<main class="wrap wrap-wide futures-main">

  <!-- PRESETS SECTION -->
  <section class="futures-section">
    <div class="section-hdr">
      <div>
        <h2>Preset Strike Teams</h2>
        <p class="muted">Instant canonical formations forged across the multiverse.</p>
      </div>
    </div>
    <div class="presets-grid">
      {preset_cards_html}
    </div>
  </section>

  <!-- CUSTOM TEAM BUILDER -->
  <section class="futures-section" id="assembler-section">
    <div class="section-hdr">
      <div>
        <h2>Custom Strike Team Assembler</h2>
        <p class="muted">Search and draft 1 to 5 champions from the 143 confirmed movie characters.</p>
      </div>
      <div class="assembler-meta">
        <span class="team-counter">Selected: <strong id="team-count">0</strong> / 5</span>
        <button id="clear-team" class="btn btn-sm btn-secondary" type="button">Clear Team</button>
      </div>
    </div>

    <!-- Search box with instant autocomplete -->
    <div class="champ-search-wrap">
      <div class="search-input-box">
        <span class="search-icon">🔍</span>
        <input id="champ-search-input" type="text" class="cmd-input" placeholder="Type a character name (e.g., Wanda, Logan, Blade, Thor, Doom)..." autocomplete="off">
      </div>
      <div id="champ-dropdown" class="champ-dropdown" style="display:none;" role="listbox"></div>
    </div>

    <!-- Selected Champions Deck -->
    <div class="team-deck" id="team-deck">
      <div class="deck-slot empty" data-slot="0"><span class="slot-plus">+</span><span>Slot 1 (Empty)</span></div>
      <div class="deck-slot empty" data-slot="1"><span class="slot-plus">+</span><span>Slot 2 (Empty)</span></div>
      <div class="deck-slot empty" data-slot="2"><span class="slot-plus">+</span><span>Slot 3 (Empty)</span></div>
      <div class="deck-slot empty" data-slot="3"><span class="slot-plus">+</span><span>Slot 4 (Empty)</span></div>
      <div class="deck-slot empty" data-slot="4"><span class="slot-plus">+</span><span>Slot 5 (Empty)</span></div>
    </div>

    <!-- THE SIMULATION CTA -->
    <div class="simulate-cta-wrap">
      <button id="run-simulation-btn" class="btn-simulate" type="button" disabled>
        <span class="rune-glyph">✦</span>
        <span class="sim-btn-text">SELECT AT LEAST 1 CHAMPION</span>
        <span class="rune-glyph">✦</span>
      </button>
      <p class="simulate-hint" id="sim-hint">Add champions above to unlock the Time Stone calculation.</p>
    </div>
  </section>

  <!-- ANIMATED TIME STONE ORB & ROLLER -->
  <section class="simulation-chamber" id="sim-chamber" style="display:none;" aria-live="polite">
    <div class="rune-mandala">
      <div class="rune-ring r-outer"></div>
      <div class="rune-ring r-mid"></div>
      <div class="rune-ring r-inner"></div>
      <div class="gem-core"><span>14M</span></div>
    </div>
    <div class="timeline-counter-box">
      <div class="counter-label">PEERING THROUGH MULTIVERSAL TIMELINES</div>
      <div class="counter-num" id="counter-display">0</div>
      <div class="counter-sub">OF 14,000,605 POTENTIAL FUTURES</div>
    </div>
  </section>

  <!-- SIMULATION RESULTS DOSSIER -->
  <section class="simulation-results" id="sim-results" style="display:none;">
    <div class="dossier-card">
      <div class="dossier-header">
        <div class="dossier-tag"><span class="pulse-dot"></span> TEMPORAL DOSSIER GENERATED</div>
        <div class="odds-banner">
          <span class="odds-val" id="result-odds">1 IN 14,000,605</span>
          <span class="odds-sub" id="result-odds-pct">0.0000071% VICTORY PROBABILITY</span>
        </div>
      </div>

      <!-- Live AI stream indicator if AI key used -->
      <div id="ai-active-badge" class="ai-stream-badge" style="display:none;">
        <span class="ai-spark">⚡</span> <span id="ai-provider-label">NVIDIA NIM Neural Inference (Llama 3.1 70B) Active</span>
      </div>

      <!-- Threat matrix -->
      <div class="dossier-section">
        <h3 class="section-title">⚔️ Tactical Threat Analysis vs God Emperor Doom</h3>
        <div class="threat-grid" id="result-threat-matrix"></div>
      </div>

      <!-- Timeline 14,000,604 -->
      <div class="dossier-section fatal-section">
        <div class="timeline-badge fatal">TIMELINE #14,000,604 &bull; FATAL NEAR-VICTORY</div>
        <h3 class="timeline-title">The Tragic Near-Victory</h3>
        <p class="timeline-narrative" id="result-fatal-narrative"></p>
      </div>

      <!-- Timeline 14,000,605 -->
      <div class="dossier-section victory-section">
        <div class="timeline-badge victory">TIMELINE #14,000,605 &bull; THE SOLE VICTORY PATH</div>
        <h3 class="timeline-title">The Sole Confluence of Victory</h3>
        <p class="timeline-narrative" id="result-victory-narrative"></p>
      </div>

      <!-- Critical divergence -->
      <div class="dossier-section divergence-section">
        <div class="divergence-tag">CRITICAL DIVERGENCE POINT</div>
        <p class="divergence-text" id="result-divergence-text"></p>
      </div>
    </div>
  </section>

</main>

<!-- API KEY CONFIGURATION MODAL -->
<div id="api-modal" class="modal-backdrop" style="display:none;" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal-card">
    <div class="modal-head">
      <h3 id="modal-title">⚙️ Connect Time Stone AI</h3>
      <button id="close-api-modal" class="modal-close" type="button" aria-label="Close dialog">&times;</button>
    </div>
    <div class="modal-body">
      <p class="muted" style="margin-bottom:1rem;font-size:0.88rem;line-height:1.5;">
        Upgrade the simulator with live AI battle chronologies! Your API key is stored strictly in your browser's <code>localStorage</code> and never shared.
      </p>

      <div class="form-group">
        <label for="ai-provider-select">Select AI Model Provider:</label>
        <select id="ai-provider-select" class="cmd-input">
          <option value="nvidia">NVIDIA NIM (meta/llama-3.1-70b-instruct) — Via local proxy or build.nvidia.com</option>
          <option value="groq">Groq (Llama 3.3 / 3.1 70B) — Free, 500 tok/s, Instant Browser CORS</option>
          <option value="gemini">Google Gemini (gemini-1.5-flash) — Free, Instant Browser CORS</option>
          <option value="openrouter">OpenRouter (Llama 3.1 70B) — Free / Bring Your Own Key</option>
        </select>
      </div>

      <div class="form-group">
        <label for="ai-key-input">Enter API Key:</label>
        <div style="display:flex;gap:0.5rem;">
          <input id="ai-key-input" type="password" class="cmd-input" placeholder="Paste your API key here..." autocomplete="off" style="flex:1;">
          <button id="toggle-key-visibility" class="btn btn-sm btn-secondary" type="button" title="Show/Hide Key">👁️</button>
        </div>
        <p class="hint-text" id="provider-hint">
          Get a free key: <a id="provider-link" href="https://build.nvidia.com" target="_blank" rel="noopener">build.nvidia.com</a> (NVIDIA) &bull; <a href="https://console.groq.com" target="_blank" rel="noopener">console.groq.com</a> (Groq) &bull; <a href="https://aistudio.google.com" target="_blank" rel="noopener">aistudio.google.com</a> (Gemini).
        </p>
      </div>

      <div class="form-group" id="model-select-group">
        <label for="ai-model-select">Selected Model (Auto-detect or Custom):</label>
        <div style="display:flex;gap:0.5rem;margin-bottom:0.4rem;">
          <select id="ai-model-select" class="cmd-input" style="flex:1;">
            <option value="">-- Click 'Fetch Models' to load your account's models --</option>
          </select>
          <button id="fetch-models-btn" class="btn btn-sm btn-outline" type="button" title="Fetch all models available for your key">Fetch Models 🔄</button>
        </div>
        <div style="display:flex;gap:0.5rem;">
          <input id="ai-custom-model-input" type="text" class="cmd-input" placeholder="Or enter exact model name (e.g. gemini-2.0-flash, gemini-4-hydrogen, gemini-3.8-flash)..." style="flex:1;">
        </div>
        <p class="hint-text">Choose from your account's detected models, or type any model identifier shown on your Google AI Studio quickstart.</p>
      </div>

      <div id="test-key-result" class="test-key-result" style="display:none;margin-bottom:1rem;"></div>

      <div class="modal-actions">
        <button id="test-key-btn" class="btn btn-secondary" type="button">Test Connection</button>
        <button id="save-key-btn" class="btn btn-primary" type="button">Save Settings</button>
        <button id="clear-key-btn" class="btn btn-secondary" type="button">Remove Key</button>
      </div>

      <div class="local-proxy-tip" id="local-proxy-tip" style="margin-top:1.25rem;padding:0.75rem;background:rgba(0,204,85,0.08);border:1px solid rgba(0,204,85,0.25);border-radius:8px;font-size:0.78rem;color:#a3e6b8;">
        💡 <strong>Tip for NVIDIA NIM keys:</strong> NVIDIA's cloud servers do not allow direct browser-to-server CORS. When testing locally, run <code>python3 scripts/serve.py</code> (which provides our automatic local proxy). For 1-click browser access without a proxy, select <strong>Groq</strong> (runs the same Llama-3.1 70B) or <strong>Google Gemini</strong>!
      </div>
    </div>
  </div>
</div>

<script id="roster-data" type="application/json">{roster_json}</script>
<script id="presets-data" type="application/json">{presets_json}</script>
<script src="../assets/js/main.js"></script>
<script src="../assets/js/futures.js"></script>
""" + ex.foot() + "</body></html>")


def build_all():
    EXPLORE.mkdir(parents=True, exist_ok=True)
    html = build_futures_page()
    (EXPLORE / "futures.html").write_text(html, encoding="utf-8")
    print("  wrote explore/futures.html (14,000,605 Futures Simulator)")


if __name__ == "__main__":
    build_all()
