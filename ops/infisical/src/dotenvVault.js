/*
 * Purpose: Load secrets locally from dotenv-vault via dotenv + DOTENV_KEY
 * Created: 2025-12-17
 * Author: GPT-5.2
 */

import dotenv from "dotenv";

/**
 * Load environment variables from dotenv-vault.
 *
 * `dotenv-vault` manages `.env.vault`; `dotenv` decrypts it when `DOTENV_KEY` is set.
 */
export function loadDotenvVault({ repoRoot }) {
  const prevCwd = process.cwd();
  try {
    if (repoRoot) process.chdir(repoRoot);

    // Reduce noisy output from dotenv in CLI contexts.
    if (!process.env.DOTENV_CONFIG_QUIET) process.env.DOTENV_CONFIG_QUIET = "true";

    // dotenv will:
    // - load `.env` if present
    // - decrypt `.env.vault` when DOTENV_KEY is provided
    dotenv.config({
      override: true,
    });

    return {
      ok: true,
      source: "dotenv-vault",
    };
  } finally {
    process.chdir(prevCwd);
  }
}

