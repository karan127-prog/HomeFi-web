/**
 * HomeFi Web App — charts.js
 * Shared Chart.js config, color palette, and utility functions.
 * Loaded on every page via base.html.
 */

// ── GLOBAL COLOR PALETTE ──
const HF = {
  green   : "#69f0ae",
  red     : "#ff5370",
  blue    : "#4fc3f7",
  yellow  : "#ffd740",
  purple  : "#b388ff",
  orange  : "#ff8a65",
  teal    : "#80cbc4",
  pink    : "#f48fb1",
  lime    : "#dce775",
  sky     : "#81d4fa",

  // Backgrounds (transparent versions)
  greenBg : "rgba(105,240,174,0.08)",
  redBg   : "rgba(255,83,112,0.08)",
  blueBg  : "rgba(79,195,247,0.08)",
  yellowBg: "rgba(255,215,64,0.08)",

  // UI colors
  surface : "#13131f",
  card    : "#1a1a2e",
  border  : "#252540",
  text    : "#e8eaf6",
  muted   : "#7986cb",

  // Category palette (10 colors)
  palette: [
    "#4fc3f7","#69f0ae","#ff5370","#ffd740",
    "#b388ff","#ff8a65","#80cbc4","#f48fb1",
    "#dce775","#81d4fa"
  ]
};

// ── CHART.JS GLOBAL DEFAULTS ──
Chart.defaults.color          = HF.muted;
Chart.defaults.borderColor    = HF.border;
Chart.defaults.font.family    = "'Space Grotesk', sans-serif";
Chart.defaults.font.size      = 12;
Chart.defaults.plugins.legend.labels.padding     = 16;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.tooltip.backgroundColor  = HF.card;
Chart.defaults.plugins.tooltip.borderColor      = HF.border;
Chart.defaults.plugins.tooltip.borderWidth      = 1;
Chart.defaults.plugins.tooltip.padding          = 10;
Chart.defaults.plugins.tooltip.titleColor       = HF.text;
Chart.defaults.plugins.tooltip.bodyColor        = HF.muted;
Chart.defaults.plugins.tooltip.cornerRadius     = 8;
Chart.defaults.scale.grid.color                 = HF.border;
Chart.defaults.scale.ticks.color                = HF.muted;


// ── UTILITY: Format rupee values ──
function fmtRs(value) {
  if (value >= 100000) return "Rs." + (value / 100000).toFixed(1) + "L";
  if (value >= 1000)   return "Rs." + (value / 1000).toFixed(1) + "k";
  return "Rs." + value.toFixed(0);
}

// ── UTILITY: Get category color by index ──
function catColor(index) {
  return HF.palette[index % HF.palette.length];
}

// ── UTILITY: Status color ──
function statusColor(status) {
  const map = {
    "EXCEEDED"    : HF.red,
    "WARNING"     : HF.yellow,
    "MODERATE"    : HF.orange,
    "GOOD"        : HF.green,
    "COMPLETED"   : HF.green,
    "ALMOST THERE": HF.blue,
    "HALFWAY"     : HF.yellow,
    "IN PROGRESS" : HF.orange,
    "JUST STARTED": HF.red,
  };
  return map[status] || HF.muted;
}

// ── UTILITY: Animate stat card numbers ──
function animateCounter(element, target, prefix = "", suffix = "", duration = 1200) {
  const start     = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed  = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current  = Math.floor(eased * target);

    element.textContent = prefix + current.toLocaleString("en-IN") + suffix;

    if (progress < 1) requestAnimationFrame(update);
    else element.textContent = prefix + target.toLocaleString("en-IN") + suffix;
  }

  requestAnimationFrame(update);
}

// ── AUTO-ANIMATE all .stat-value elements on page load ──
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".stat-value").forEach(el => {
    const text = el.textContent.trim();

    // Extract number from text like "Rs.1,17,600" or "39.86%"
    const numMatch = text.match(/[\d,]+\.?\d*/);
    if (!numMatch) return;

    const num    = parseFloat(numMatch[0].replace(/,/g, ""));
    const prefix = text.startsWith("Rs.") ? "Rs." : "";
    const suffix = text.endsWith("%") ? "%" : "";

    if (!isNaN(num) && num > 0) {
      animateCounter(el, num, prefix, suffix, 1000);
    }
  });
});

// ── SHARED: Standard line chart options ──
function lineChartOptions(yFormatter) {
  return {
    responsive         : true,
    maintainAspectRatio: false,
    interaction        : { mode: "index", intersect: false },
    plugins: {
      legend: { labels: { color: HF.text } },
      tooltip: {
        callbacks: {
          label: ctx => ` ${ctx.dataset.label}: Rs.${ctx.parsed.y.toLocaleString("en-IN")}`
        }
      }
    },
    scales: {
      x: { ticks: { color: HF.muted }, grid: { color: HF.border } },
      y: {
        ticks: {
          color   : HF.muted,
          callback: yFormatter || (v => fmtRs(v))
        },
        grid: { color: HF.border }
      }
    }
  };
}

// ── SHARED: Standard bar chart options ──
function barChartOptions(yFormatter) {
  return {
    responsive         : true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: HF.text } }
    },
    scales: {
      x: { ticks: { color: HF.muted }, grid: { color: HF.border } },
      y: {
        ticks: {
          color   : HF.muted,
          callback: yFormatter || (v => fmtRs(v))
        },
        grid: { color: HF.border }
      }
    }
  };
}