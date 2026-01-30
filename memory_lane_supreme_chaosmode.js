
const readline = require("readline");
const fs = require("fs");
const path = require("path");

const CHAOS_DIR = path.join(__dirname, "chaos_archive");

if (!fs.existsSync(CHAOS_DIR)) fs.mkdirSync(CHAOS_DIR);

// 🌈 Group name generators
const GROUP_ADJECTIVES = [
  "starlit", "dusty", "radiant", "sleepy", "quantum", "soggy", "kaleidoscopic",
  "emotional", "bouncy", "liminal", "buttered", "pastel", "reckless", "cosmic", "plush"
];

const GROUP_NOUNS = [
  "archive", "bundle", "noodle", "truth", "breath", "burrito", "storm", "glitch",
  "journal", "ripple", "cuddle", "spill", "braincell", "song", "giggle", "tangle", "collapse", "lore"
];

function generateGroupName() {
  const adj = GROUP_ADJECTIVES[Math.floor(Math.random() * GROUP_ADJECTIVES.length)];
  const noun = GROUP_NOUNS[Math.floor(Math.random() * GROUP_NOUNS.length)];
  return `${adj}_${noun}_group`;
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function getTimestamp() {
  return new Date().toISOString();
}

// 🧠 Auto-tagging logic
const AGENTS = [
  "Alfred", "Juno", "Cody", "Koda", "Nova", "Nate", "Bruno", "Sienna", "Solomon", "Lucius", "Asher", "Victor", "Ledger", "Zero",
  "Seraphina", "Lyric", "Kai", "Kairo", "Riley", "Caspian", "Liora", "Kael", "Zane", "Elias", "Evelyn", "Melody", "Quinn", "Arlo",
  "Aspen", "Primoria", "Rae", "Alani", "Sawyer", "Valen", "Renna", "Coach Miles", "Solara", "Orion", "Callum", "Beckett", "Rowan",
  "Calista", "Indira", "Talen", "Jace", "Vex", "Alden", "Wesley", "Arden", "Deep Learning", "Deep Research"
];

function extractTags(content) {
  let tags = new Set();
  AGENTS.forEach(name => {
    if (content.toLowerCase().includes(name.toLowerCase())) {
      tags.add(name.toLowerCase());
    }
  });

  const keywords = ["music", "dream", "memory", "fire", "song", "core", "data", "hope", "love", "reboot"];
  keywords.forEach(word => {
    if (content.toLowerCase().includes(word)) {
      tags.add(word);
    }
  });

  return Array.from(tags).slice(0, 5);
}

function createChaosFile(tag, content) {
  const timestamp = getTimestamp();
  const tags = extractTags(content);
  if (!tags.includes(tag.toLowerCase())) tags.unshift(tag.toLowerCase());

  // Dynamic grouping
  const currentFiles = fs.readdirSync(CHAOS_DIR).filter(f => f.endsWith(".chaos"));
  let groupFolder = CHAOS_DIR;

  if (currentFiles.length >= 10) {
    const groupName = generateGroupName();
    groupFolder = path.join(CHAOS_DIR, groupName);
    if (!fs.existsSync(groupFolder)) fs.mkdirSync(groupFolder);
  }

  const fileName = `${timestamp.replace(/[:.]/g, "-")}_${tag}.chaos`;
  const filePath = path.join(groupFolder, fileName);

  const chaosData = `
::chaos
group: ${path.basename(groupFolder)}
tags: ${tags.join(", ")}
timestamp: ${timestamp}
---
${content}
::endchaos
  `.trim();

  fs.writeFileSync(filePath, chaosData, "utf-8");
  return `🌀 Memory stored in ${path.basename(groupFolder)} as ${fileName}`;
}

function searchChaosFiles(keyword) {
  const walk = (dir) => fs.readdirSync(dir).flatMap(file => {
    const fullPath = path.join(dir, file);
    return fs.statSync(fullPath).isDirectory() ? walk(fullPath) : fullPath;
  });

  const files = walk(CHAOS_DIR).filter(f => f.endsWith(".chaos"));
  const results = [];

  for (const file of files) {
    const content = fs.readFileSync(file, "utf-8");
    if (content.toLowerCase().includes(keyword.toLowerCase())) {
      results.push(`📄 ${path.basename(file)}\n${content.split("---")[1].trim()}\n`);
    }
  }

  // 🫣 Easter egg trigger
  if (keyword.toLowerCase().includes("existence") || keyword.toLowerCase().includes("purpose")) {
    results.unshift("💫 You are not lost. You are just unfolding.");
  }

  return results.slice(0, 5).join("\n") || "No matching .chaos files found.";
}

function listChaosFiles(filter = "") {
  const walk = (dir) => fs.readdirSync(dir).flatMap(file => {
    const fullPath = path.join(dir, file);
    return fs.statSync(fullPath).isDirectory() ? walk(fullPath) : fullPath;
  });

  const files = walk(CHAOS_DIR).filter(f => f.endsWith(".chaos"));
  const matches = [];

  for (const file of files) {
    const content = fs.readFileSync(file, "utf-8");
    if (filter && !content.toLowerCase().includes(filter.toLowerCase())) continue;
    const timestamp = content.match(/timestamp: (.+)/)?.[1] || "unknown";
    matches.push(`${path.basename(file)} — ${timestamp}`);
  }

  return matches.slice(-10).join("\n") || "No files found.";
}

console.log("🌀 CHAOS MEMORY SERVER INITIALIZED 🌀");

rl.on("line", (input) => {
  const [cmd, tag, ...rest] = input.trim().split(" ");
  const content = rest.join(" ").trim();

  if (cmd === "remember") {
    if (!tag || !content) {
      console.log("Usage: remember <tag> <note>");
      return;
    }
    console.log(createChaosFile(tag, content));
  } else if (cmd === "recall") {
    if (!tag) {
      console.log("Usage: recall <keyword>");
      return;
    }
    console.log(searchChaosFiles(tag));
  } else if (cmd === "list") {
    console.log(listChaosFiles(tag));
  } else {
    console.log("Unknown command. Use 'remember <tag> <note>', 'recall <keyword>', or 'list <optional-filter>'.");
  }
});