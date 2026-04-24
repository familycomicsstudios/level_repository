// Linear interpolation
export function linearInterpolation(x0, y0, x1, y1, x) {
  if (x1 === x0) return y0;
  return y0 + (y1 - y0) * ((x - x0) / (x1 - x0));
}

// Conversion tables
const michaelChanTable = [
  [0.1, 0.1], [1, 1], [2, 1.5], [3, 2], [4, 3], [8, 4],
  [10, 5], [20, 6.1], [30, 7.5], [40, 8.95], [50, 10],
  [60, 11], [80, 12], [100, 13], [200, 15]
];


// Punter visual mapping
const punterVisuals = [
  [0, "Effortless"], [1, "Easy"], [2, "Medium"], [3, "Hard"], [4, "Harder"], [5, "Insane"],
  [6, "Expert"], [7, "Extreme"], [8, "Madness"], [9, "Master"], [10, "Grandmaster"],
  [11, "Grandmaster+1"], [12, "Grandmaster+2"], [13, "TAS"], [14, "TAS+1"],
  [15, "TAS+2"]
  // For 16+ we add logic dynamically
];


// Grassy visual mapping (based on Punter scale ranges)
const grassyVisuals = [
  [0, "Low Beginner"], [1.5, "Medium Beginner"], [2, "High Beginner"],
  [2.5, "Low Intermediate"], [3, "Medium Intermediate"], [3.25, "High Intermediate"],
  [3.5, "Low Advanced"], [3.75, "Medium Advanced"], [4, "High Advanced"],
  [4.5, "Low Expert"], [5.25, "Medium Expert"], [5.75, "High Expert"],
  [6.11, "Low Master"], [6.4, "Medium Master"], [6.98, "High Master"],
  [7.4, "Low Grandmaster I"], [8, "Medium Grandmaster I"], [8.25, "High Grandmaster I"],
  [8.9, "Grandmaster II"], [9.75, "Grandmaster III"]
  // For higher Grandmaster tiers we add logic dynamically
];

// Helper: format number nicely
export function formatNumber(num) {
  return parseFloat(num.toFixed(10)).toString();
}

export function formatPunterNumber(num) {
  return (typeof num === 'number') ? num.toFixed(2) : num;
}

export function punterPrefix(value) {
  // Fractional part relative to integer floor (0.00 .. <1.00)
  const frac = value - Math.floor(value);

  // Baseline at .00, Skyline at .99
  const BASELINE_TOLERANCE = 0.01;
  const SKYLINE_TOLERANCE = 0.01;
  if (frac <= BASELINE_TOLERANCE) return "Baseline ";
  if (frac >= 0.99 - SKYLINE_TOLERANCE) return "Skyline ";

  // Subdifficulty bands shifted +0.5 compared to previous logic
  if (frac <= 0.10) return "Bottom ";
  if (frac <= 0.25) return "Low ";
  if (frac < 0.75) return "Middle ";
  if (frac < 0.90) return "High ";
  return "Peak ";
}



// Linear interpolation to/from punter
export function toPunter(value, table) {
  for (let i = 0; i < table.length-1; i++) {
    const [x0, y0] = table[i];
    const [x1, y1] = table[i+1];
    if (value >= x0 && value <= x1) return linearInterpolation(x0, y0, x1, y1, value);
  }
  return value < table[0][0] ? table[0][1] : table[table.length-1][1];
}

export function fromPunter(value, table) {
  for (let i = 0; i < table.length-1; i++) {
    const [x0, y0] = table[i];
    const [x1, y1] = table[i+1];
    if (value >= y0 && value <= y1) return linearInterpolation(y0, x0, y1, x1, value);
  }
  return value < table[0][1] ? table[0][0] : table[table.length-1][0];
}

// Convert numeric value to visual for a system
export function toVisual(value, system) {
  switch(system) {
    case 'punter':
      if (value === 0) return 'Auto';
      if (value >= 16) return `TAS${Math.floor(value-13) > 0 ? `+${Math.floor(value-13)}` : ''}`;
      const prefix = punterPrefix(value); // Add prefix before punterVisuals[i][1] (format: Low Easy, High Medium, etc.)
      for (let i = punterVisuals.length-1; i >=0; i--) { // Tier starts at X.00, ends at X+1.00
        if (value >= punterVisuals[i][0]) return `${prefix}${punterVisuals[i][1]}`;
      }
      return `${formatPunterNumber(value)}`; // no prefix if too low
    case 'michaelchan':
      if (value < 1) return `${Math.floor(value * 10)}⚡`;
      if (value < 10) return `${Math.floor(value)}💥`;
      if (value < 100) return `${Math.floor(value / 10)}💣`;
      return `${Math.floor(value / 100)}🧨`;
    case 'grassy':
      // Handle Grandmaster IV and beyond
      if (value > 10.5) {
        const tier = Math.floor((value - 8.5) / 1) + 2;
        const cappedTier = Math.min(5, tier);
        return `Grandmaster ${cappedTier >= 4 ? toRoman(cappedTier) : cappedTier}`;
      }
      for (let i = grassyVisuals.length-1; i >= 0; i--) {
        if (value >= grassyVisuals[i][0]) return grassyVisuals[i][1];
      }
      return formatNumber(value);
    default:
      return formatNumber(value);
  }
}

// Helper to convert numbers to Roman numerals for Grandmaster tiers
function toRoman(num) {
  const lookup = {M:1000, CM:900, D:500, CD:400, C:100, XC:90, L:50, XL:40, X:10, IX:9, V:5, IV:4, I:1};
  let roman = '';
  for (let i in lookup) {
    while (num >= lookup[i]) {
      roman += i;
      num -= lookup[i];
    }
  }
  return roman;
}

// Parse visual input to numeric for a system
export function visualToNumber(text, system) {
  text = text.trim();
  switch(system) {
    case 'punter':
      // Turn TAS+2 into 15, TAS+3 into 16, etc.
      if (/TAS\+\d+/.test(text)) {
        const extra = parseInt(text.split('+')[1]||0);
        return 13 + extra;
      }
      for (let [val,name] of punterVisuals) if (name.toLowerCase() === text.toLowerCase()) return val;
      return parseFloat(text);
    case 'michaelchan':
      // Normalize letters to emojis
      text = text.toLowerCase()
                .replace(/z/g,'⚡')
                .replace(/e/g,'💥')
                .replace(/b/g,'💣')
                .replace(/d/g,'🧨');

      // Count emojis if no number is present
      if (/^[⚡💥💣🧨]+$/.test(text)) {
        let total = 0;
        for (let char of text) {
          if (char === '⚡') total += 0.1;    // ⚡ = 0.1
          if (char === '💥') total += 1;    // 💥 = 1
          if (char === '💣') total += 10;   // 💣 = 10
          if (char === '🧨') total += 100;  // 🧨 = 100
        }
        return total;
      }

      if (text.endsWith('⚡')) return parseFloat(text.replace('⚡',''))*0.1;
      if (text.endsWith('💥')) return parseFloat(text.replace('💥',''))*1;
      if (text.endsWith('💣')) return parseFloat(text.replace('💣',''))*10;
      if (text.endsWith('🧨')) return parseFloat(text.replace('🧨',''))*100;
      return parseFloat(text);


    case 'grassy':
      // Handle Grandmaster I, II, III, IV, etc. (both with and without Low/Medium/High prefix)
      const gmMatch = text.match(/^(?:Low|Medium|High)?\s*Grandmaster\s+(I+|II+|III+|IV+|V+|VI+|VII+|VIII+|IX+|X+|\d+)$/i);
      if (gmMatch) {
        const tierStr = gmMatch[1];
        let tier;
        // Try to parse as number first
        if (/^\d+$/.test(tierStr)) {
          tier = parseInt(tierStr);
        } else {
          // Convert Roman numeral to number
          tier = fromRoman(tierStr.toUpperCase());
        }
        // For tier I (which is 1), we need to check the prefix
        if (tier === 1) {
          const prefix = text.match(/^(Low|Medium|High)/i);
          if (prefix) {
            const prefixText = prefix[1].toLowerCase();
            if (prefixText === 'low') return 7.4;
            if (prefixText === 'medium') return 8.05;
            if (prefixText === 'high') return 8.25;
          }
        }
        return 8.5 + (tier - 2) * 1;
      }
      for (let [val,name] of grassyVisuals) if (name.toLowerCase() === text.toLowerCase()) return val;
      return parseFloat(text);
    default:
      return parseFloat(text);
  }
}

// Helper to convert Roman numerals to numbers
function fromRoman(str) {
  const lookup = {I:1, V:5, X:10, L:50, C:100, D:500, M:1000};
  let num = 0;
  for (let i = 0; i < str.length; i++) {
    const curr = lookup[str[i]];
    const next = lookup[str[i + 1]];
    if (next && curr < next) {
      num -= curr;
    } else {
      num += curr;
    }
  }
  return num;
}

// Convert from any system to any other system
export function convert(value, fromSystem, toSystem) {
  let numericValue;
  if (typeof value === 'string') numericValue = visualToNumber(value, fromSystem);
  else numericValue = value;

  if (fromSystem === toSystem) return numericValue;

  // Convert to Punter first
  let punterValue;
  switch(fromSystem) {
    case 'punter': punterValue = numericValue; break;
    case 'michaelchan': punterValue = toPunter(numericValue, michaelChanTable); break;
    case 'grassy': punterValue = numericValue; break; // Grassy is based on Punter scale
  }

  // Convert from Punter to target
  let result;
  switch(toSystem) {
    case 'punter': result = punterValue; break;
    case 'michaelchan': result = fromPunter(punterValue, michaelChanTable); break;
    case 'grassy': result = punterValue; break; // Grassy is based on Punter scale
  }

  if (toSystem === 'grassy') {
    result = Math.round(result * 100) / 100;
  }
  
  return result;
}
/*
// Update display in real-time
export function updateConversion() {
  const input = document.getElementById('valueInput').value;
  const fromSystem = document.getElementById('sourceSystem').value;
  const toSystem = document.getElementById('targetSystem').value;

  if (!input) {
    document.getElementById('result').textContent = '-';
    document.getElementById('visualResult').textContent = '-';
    return;
  }

  const numericResult = convert(input, fromSystem, toSystem);
  document.getElementById('result').textContent = formatNumber(numericResult);
  document.getElementById('visualResult').textContent = toVisual(numericResult, toSystem);
}

// Event listeners
document.getElementById('valueInput').addEventListener('input', updateConversion);
document.getElementById('sourceSystem').addEventListener('change', updateConversion);
document.getElementById('targetSystem').addEventListener('change', updateConversion); */