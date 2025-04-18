# html_trainer.py
"""
Generate an interactive HTML training page from the chord mapping.
"""
import json
import argparse

special_keys = {
    "delete_word",
    "ing", "ed", "er", "ly", "ment", "ness", "ship",
    "able", "ion", "ity", "ous", "est", "ive", "less",
    "un", "re", "pre", "anti",
}

def main():
    parser = argparse.ArgumentParser(description="HTML trainer generator")
    parser.add_argument("--map", default="mapping.json", help="Input chord mapping JSON")
    parser.add_argument("--out", default="chart.html", help="Output HTML file")
    args = parser.parse_args()

    with open(args.map, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # Build main and special data
    main_chart_data = []
    special_chart_data = []
    for word, chord in mapping.items():
        chord_str = chord if isinstance(chord, str) else "".join(chord)
        disp = chord_str.lower()
        if word in special_keys:
            special_chart_data.append({"word": word, "chord": disp})
        else:
            main_chart_data.append({"word": word, "chord": disp})
    # frequency rank
    for idx, item in enumerate(main_chart_data):
        item["rank"] = idx + 1

    frequencyData = main_chart_data
    alphabeticalData = sorted(main_chart_data, key=lambda x: x["word"].lower())

    # Summary
    count2 = sum(1 for c in mapping.values() if len(c if isinstance(c, str) else "".join(c)) == 2)
    count3 = sum(1 for c in mapping.values() if len(c if isinstance(c, str) else "".join(c)) == 3)
    count4 = sum(1 for c in mapping.values() if len(c if isinstance(c, str) else "".join(c)) == 4)
    total_assigned = len(mapping)
    header_info = (
        f"<p style='color: #444; font-size: 0.9em;'>"
        f"Chords assigned: {total_assigned}<br>"
        f"2-letter: {count2}, 3-letter: {count3}, 4-letter: {count4}</p>"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Chord Mapping Chart</title>
  <style>
    body {{
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 20px;
      background-color: #222;
      color: #eee;
      max-width: 700px;
      margin: auto;
      border-radius: 8px;
      overflow-y: auto;
    }}
    h1 {{
      text-align: center;
    }}
    
    
    
    /* Reminder section styling (no border, more rounded) */
    #reminder {{
      font-size: 0.8em;
      display: flex;
      justify-content: space-between;
      margin: 20px 0 1em;
      padding: 10px;
      border-radius: 32px;
      background-color: #111;
      color: #666;
      width: 140%;
      margin-left: -20%;
      box-sizing: border-box;
    }}
    /* clickable commands: pill always there with matching size */
    code.cmd {{
      cursor: pointer;
      color: #444;
      font-family: inherit;
      font-size: 1em;
      display: inline-block;
      padding: 4px 8px;          /* keeps pill shape even when transparent */
      border-radius: 16px;
      background-color: transparent;
      transition: background-color 0.3s, color 0.3s;
    }}
    /* pill “fills in” on click */
    code.cmd.clicked {{
      background-color: #444;
      color: #eee;
    }}
    
    
    
    /* Chording Test styling */
    #typingTestContainer {{
      margin-bottom: 20px;
      background-color: #2e2e2e;
      border: none;
      border-radius: 24px;
      position: relative;
      width: 140%;
      margin-left: -20%;
      margin-right: -20%;
      box-sizing: border-box;
      padding: 40px 30px;
    }}
    /* 1px border now shown via an inset box-shadow when active, so layout doesn't shift */
    #typingTestContainer:focus-within {{
      box-shadow: inset 0 0 0 1px #444;
    }}
    /* WPM Display pill */
    #wpmDisplay {{
      position: absolute;
      top: 12px;
      right: 10px;
      font-size: 1.2rem;
      line-height: 1.2em;
      padding: 4px 10px;
      border-radius: 9999px;
      background-color: #444;
      color: #222;
    }}
    /* Entire container is clickable */
    #typingTestContainer:hover {{
      cursor: text;
    }}
    #typingLine {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      outline: none;
      user-select: none;
      padding: 0 10px;
      font-size: 1.3em;
      margin-top: 20px;
      border-radius: 4px;
    }}
    /* Removed the extra outline from typingLine */
    #typingLine:focus {{
      outline: none;
    }}
    .testPair {{
      display: inline-flex;
      flex-direction: column;
      margin-bottom: 10px;
      margin-right: 10px;
    }}
    .testChord {{
      font-size: 0.8em;
      color: #bbb;
      text-align: center;
      margin-bottom: 5px;
    }}
    .testWord {{
      display: flex;
    }}
    .testLetter {{
      border-bottom: 2px solid transparent;
      transition: color 0.1s;
    }}
    .activeLetter {{
      border-bottom-color: #bbb;
      animation: blink 1s infinite;
    }}
    @keyframes blink {{
      0%,50%   {{ border-bottom-color: #bbb; }}
      51%,100% {{ border-bottom-color: transparent; }}
    }}
    .correct {{
      color: #b5e853;
    }}
    .incorrect {{
      color: #ff635f;
    }}
    table {{
      border-collapse: separate;
      border-spacing: 0;
      width: 100%;
      margin-bottom: 20px;
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      padding: 10px 15px;
      text-align: left;
    }}
    /* Narrow first column for freq */
    th:first-child, td:first-child {{
      width: 10ch;
      text-align: left;
      color: #bbb;
    }}
    th {{
      background-color: #333;
      cursor: pointer;
      color: #bbb;
    }}
    th.activeSort {{
      color: #fff;
    }}
    tr:nth-child(even) {{
      background-color: #2a2a2a;
    }}
    tr:nth-child(odd) {{
      background-color: #252525;
    }}
    tr:hover {{
      background-color: #444;
      cursor: pointer;
    }}
    tr.selected {{
      background-color: #666;
    }}
    input[type="text"] {{
      width: 100%;
      box-sizing: border-box;
      padding: 8px;
      margin-bottom: 10px;
      background-color: #333;
      color: #eee;
      border: 1px solid #444;
      border-radius: 8px;
    }}
    /* CHORDS FONT STYLE */
    .testChord,
    #chartTable td:nth-child(3),
    #specialTable td:nth-child(2) {{
      font-size: 0.8em;
      color: #b8af97;
      text-transform: uppercase;
      font-weight: bold;
    }}
    
        /* slightly larger table text */
    #chartTable th, #chartTable td,
    #specialTable th, #specialTable td {{
      font-size: 1.1em;
    }}

  </style>
</head>
<body>

  <!-- Reminder Section -->
  <div id="reminder" onclick="document.getElementById('typingLine').focus();">
    <code class="cmd"
          data-cmd="python chordgen.py --words 5000-words.txt --out mapping.json"
          onclick="copyCommand(this)">❶ GENERATE MAPPING</code>
    <code class="cmd"
          data-cmd="python zmk_codegen.py --map mapping.json --keymap totem.keymap --out combos.keymap"
          onclick="copyCommand(this)">❷ BUILD COMBOS</code>
    <code class="cmd"
          data-cmd="python html_trainer.py --map mapping.json --out chart.html"
          onclick="copyCommand(this)">❸ CREATE CHART</code>
  </div>



  <h1>Chord Mapping Chart</h1>

  <!-- Chording Test Container -->
  <div id="typingTestContainer" onclick="document.getElementById('typingLine').focus();">
    <div id="wpmDisplay">- WPM</div>
    <div id="typingLine" tabindex="0"></div>
  </div>

  {header_info}

  <input type="text" id="search" placeholder="Search for a word..." onkeyup="filterTable()">

  <table id="chartTable">
    <thead>
      <tr>
        <th id="freqHeader">Freq</th>
        <th id="wordHeader">Word</th>
        <th>Chord</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <h2>Special Mappings</h2>
  <table id="specialTable">
    <thead>
      <tr>
        <th>Word</th>
        <th>Chord</th>
      </tr>
    </thead>
    <tbody>
      {"".join(f"<tr><td>{word}</td><td>{''.join(chord) if isinstance(chord, list) else chord}</td></tr>" for word, chord in mapping.items() if word in special_keys)}
    </tbody>
  </table>

  <script>
    function hexToRgb(hex) {{
       hex = hex.replace(/^#/, '');
       if (hex.length === 3) {{
         hex = hex.split('').map(c => c + c).join('');
       }}
       let bigint = parseInt(hex, 16);
       let r = (bigint >> 16) & 255;
       let g = (bigint >> 8) & 255;
       let b = bigint & 255;
       return {{r: r, g: g, b: b}};
    }}

    function rgbToHex(r, g, b) {{
       return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
    }}

    function interpolateColor(color1, color2, fraction) {{
       let c1 = hexToRgb(color1);
       let c2 = hexToRgb(color2);
       let r = Math.round(c1.r + (c2.r - c1.r) * fraction);
       let g = Math.round(c1.g + (c2.g - c1.g) * fraction);
       let b = Math.round(c1.b + (c2.b - c1.b) * fraction);
       return rgbToHex(r, g, b);
    }}

    // WPM breakpoints and colors
    const wpmBreakpoints = [0, 50, 100, 200, 500];
    const wpmColors = ["#CC3333", "#CCCC33", "#33CC33", "#33CCCC", "#99CCFF"];

    function getWpmColor(wpm) {{
       if (wpm <= wpmBreakpoints[0]) return wpmColors[0];
       if (wpm >= wpmBreakpoints[wpmBreakpoints.length - 1]) return wpmColors[wpmColors.length - 1];
       for (let i = 0; i < wpmBreakpoints.length - 1; i++) {{
         if (wpm >= wpmBreakpoints[i] && wpm < wpmBreakpoints[i+1]) {{
           let frac = (wpm - wpmBreakpoints[i]) / (wpmBreakpoints[i+1] - wpmBreakpoints[i]);
           return interpolateColor(wpmColors[i], wpmColors[i+1], frac);
         }}
       }}
       return wpmColors[wpmColors.length - 1];
    }}

    const alphabeticalData = {json.dumps(alphabeticalData)};
    const frequencyData = {json.dumps(frequencyData)};
    const specialWords = {json.dumps(list(special_keys))};
    
    const selectedWords = {{}};
    let currentSort = "frequency";
    let testStartTime = null;

    function updateHeaderHighlight() {{
      if (currentSort === "frequency") {{
         document.getElementById("freqHeader").classList.add("activeSort");
         document.getElementById("wordHeader").classList.remove("activeSort");
      }} else {{
         document.getElementById("freqHeader").classList.remove("activeSort");
         document.getElementById("wordHeader").classList.add("activeSort");
      }}
    }}

    function getTestWords() {{
      const rows = document.querySelectorAll("#chartTable tbody tr");
      let selected = [];
      rows.forEach(row => {{
        const word = row.cells[1].textContent;
        if (row.classList.contains("selected")) {{
          selected.push({{ word: word, chord: row.cells[2].textContent }});
        }}
      }});
      if (selected.length === 0) {{
        const pool = frequencyData.slice();
        pool.sort(() => 0.5 - Math.random());
        return pool.slice(0, 7);
      }} else {{
        while (selected.length < 7) {{
          selected.push(selected[Math.floor(Math.random() * selected.length)]);
        }}
        if (selected.length > 7) {{
          selected.sort(() => 0.5 - Math.random());
          return selected.slice(0, 7);
        }}
        return selected;
      }}
    }}

    function updateTestSection() {{
      testWords = getTestWords();
      renderTypingLine();
    }}

    function setupRowClicks() {{
      const rows = document.querySelectorAll("#chartTable tbody tr");
      rows.forEach(row => {{
        row.addEventListener("click", () => {{
          row.classList.toggle("selected");
          updateTestSection();
          applyZebra();
        }});
      }});
    }}

    function populateTable(data) {{
      const tbody = document.getElementById("chartTable").querySelector("tbody");
      tbody.innerHTML = "";
      data.forEach(item => {{
        const row = document.createElement("tr");
        const tdRank = document.createElement("td");
        tdRank.textContent = item.rank;
        const tdWord = document.createElement("td");
        tdWord.textContent = item.word;
        const tdChord = document.createElement("td");
        tdChord.textContent = item.chord;
        row.appendChild(tdRank);
        row.appendChild(tdWord);
        row.appendChild(tdChord);
        tbody.appendChild(row);
      }});
      setupRowClicks();
    }}

    function applyZebra() {{
      const tbody = document.getElementById("chartTable").querySelector("tbody");
      const visibleRows = Array.from(tbody.querySelectorAll("tr")).filter(row => row.style.display !== "");
      visibleRows.forEach((row, index) => {{
        if (row.classList.contains("selected")) {{
          row.style.backgroundColor = "";
        }} else {{
          row.style.backgroundColor = (index % 2 === 0) ? "#252525" : "#2a2a2a";
        }}
      }});
    }}

    function updateTable() {{
      const data = (currentSort === "alphabetical") ? alphabeticalData : frequencyData;
      populateTable(data);
      filterTable();
      const rows = document.querySelectorAll("#chartTable tbody tr");
      rows.forEach(row => {{
        const word = row.cells[1].textContent;
        if (selectedWords[word]) {{
          row.classList.add("selected");
        }}
      }});
      applyZebra();
      updateTestSection();
      updateHeaderHighlight();
    }}

    function filterTable() {{
      const filter = document.getElementById("search").value.toLowerCase();
      const rows = document.getElementById("chartTable").getElementsByTagName("tr");
      for (let i = 1; i < rows.length; i++) {{
        const td = rows[i].getElementsByTagName("td")[1];
        if (td) {{
          const txt = td.textContent || td.innerText;
          rows[i].style.display = txt.toLowerCase().includes(filter) ? "" : "none";
        }}
      }}
      applyZebra();
    }}

    // Typing Test Section
    let testWords = getTestWords();
    let letterSpans = [];
    let currentWordIndex = 0;
    let typedSoFar = "";
    const typingLine = document.getElementById("typingLine");

    function renderTypingLine() {{
      typingLine.innerHTML = "";
      letterSpans = [];
      currentWordIndex = 0;
      typedSoFar = "";
      testWords.forEach(item => {{
        const pair = document.createElement("div");
        pair.className = "testPair";
        const chordDiv = document.createElement("div");
        chordDiv.className = "testChord";
        chordDiv.textContent = item.chord;
        const wordDiv = document.createElement("div");
        wordDiv.className = "testWord";
        const spansForWord = [];
        item.word.split("").forEach(letter => {{
          const span = document.createElement("span");
          span.className = "testLetter";
          span.textContent = letter;
          wordDiv.appendChild(span);
          spansForWord.push(span);
        }});
        letterSpans.push(spansForWord);
        pair.appendChild(chordDiv);
        pair.appendChild(wordDiv);
        typingLine.appendChild(pair);
      }});
      highlightCurrentWord();
    }}

    function highlightCurrentWord() {{
      letterSpans.forEach(spans => spans.forEach(span => span.classList.remove("activeLetter")));
      if (document.activeElement !== typingLine) return;
      if (currentWordIndex < letterSpans.length) {{
        const spans = letterSpans[currentWordIndex];
        const idx = typedSoFar.length < spans.length ? typedSoFar.length : spans.length - 1;
        spans[idx].classList.add("activeLetter");
      }}
    }}

    function checkWord(typedWord) {{
      if (currentWordIndex >= letterSpans.length) return;
      const correct = testWords[currentWordIndex].word;
      const spans = letterSpans[currentWordIndex];
      for (let i = 0; i < spans.length; i++) {{
        if (i < typedWord.length && typedWord[i] === correct[i]) {{
          spans[i].classList.add("correct");
        }} else {{
          spans[i].classList.add("incorrect");
        }}
      }}
    }}

    function updateCurrentWordHighlight() {{
      if (currentWordIndex >= letterSpans.length) return;
      const correct = testWords[currentWordIndex].word;
      const spans = letterSpans[currentWordIndex];
      spans.forEach(span => span.classList.remove("correct", "incorrect"));
      for (let i = 0; i < typedSoFar.length && i < spans.length; i++) {{
        if (typedSoFar[i] === correct[i]) {{
          spans[i].classList.add("correct");
        }} else {{
          spans[i].classList.add("incorrect");
        }}
      }}
      highlightCurrentWord();
    }}

    typingLine.addEventListener("keydown", evt => {{
      if (currentWordIndex >= testWords.length) return;
      if (testStartTime === null && evt.key.length === 1 && typedSoFar.length === 0) {{
        testStartTime = Date.now();
      }}
      if (evt.ctrlKey && evt.key === "Backspace") {{
        typedSoFar = "";
        updateCurrentWordHighlight();
        evt.preventDefault();
        return;
      }}
      if (evt.key === "Backspace") {{
        typedSoFar = typedSoFar.slice(0, -1);
        updateCurrentWordHighlight();
        evt.preventDefault();
        return;
      }}
      if (evt.key === " ") {{
        checkWord(typedSoFar);
        typedSoFar = "";
        currentWordIndex++;
        if (currentWordIndex >= testWords.length) {{
          let elapsed = (Date.now() - testStartTime) / 60000;
          let totalChars = testWords.reduce((acc, item) => acc + item.word.length, 0);
          let wpm = (totalChars / 5) / elapsed;
          let wpmColor = getWpmColor(wpm);
          let wpmDisplay = document.getElementById("wpmDisplay");
          wpmDisplay.textContent = wpm.toFixed(1) + " WPM";
          wpmDisplay.style.backgroundColor = wpmColor;
          testStartTime = null;
          testWords = getTestWords();
          renderTypingLine();
        }} else {{
          highlightCurrentWord();
        }}
        evt.preventDefault();
        return;
      }}
      if (evt.key.length === 1 && !evt.metaKey && !evt.altKey && !evt.ctrlKey) {{
        typedSoFar += evt.key;
        updateCurrentWordHighlight();
        evt.preventDefault();
      }}
    }});

    typingLine.addEventListener("focus", highlightCurrentWord);
    typingLine.addEventListener("blur", () => {{
      letterSpans.forEach(spans => spans.forEach(span => span.classList.remove("activeLetter")));
    }});

    renderTypingLine();
    typingLine.focus();

    document.getElementById("freqHeader").addEventListener("click", function() {{
      currentSort = "frequency";
      updateTable();
    }});
    document.getElementById("wordHeader").addEventListener("click", function() {{
      currentSort = "alphabetical";
      updateTable();
    }});

    updateTable();
    
     // copy a command and show pill feedback
    function copyCommand(el) {{
      const cmd = el.dataset.cmd;
      navigator.clipboard.writeText(cmd).then(() => {{
        el.classList.add('clicked');
        setTimeout(() => {{ el.classList.remove('clicked'); }}, 1000);
      }}).catch(err => console.error("Copy failed:", err));
    }}



  </script>
</body>
</html>
"""


    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Written HTML trainer to {args.out}")

if __name__ == "__main__":
    main()