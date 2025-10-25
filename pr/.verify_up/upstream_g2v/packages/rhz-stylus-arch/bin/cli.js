#!/usr/bin/env node
import { architecture, llmGuide } from "../index.js";

const arg = process.argv[2] || "all";

if (arg === "--llm" || arg === "llm") {
  console.log(llmGuide);
} else if (arg === "--arch" || arg === "arch") {
  console.log(architecture);
} else {
  console.log(architecture);
  console.log("\n--- LLM Usage Guide ---\n");
  console.log(llmGuide);
}

