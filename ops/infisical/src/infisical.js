/*
 * Purpose: Fetch secrets from Infisical using Universal Auth (Machine Identity)
 * Created: 2025-12-17
 * Author: GPT-5.2
 */

import { InfisicalSDK } from "@infisical/sdk";

/**
 * Fetch all secrets from Infisical for a given project/environment/path.
 *
 * Security: never log secret values.
 */
export async function fetchInfisicalSecrets({
  siteUrl,
  clientId,
  clientSecret,
  projectId,
  environment,
  path = "/",
}) {
  if (!clientId || !clientSecret) {
    throw new Error("Missing INFISICAL_CLIENT_ID/INFISICAL_CLIENT_SECRET");
  }
  if (!projectId || !environment) {
    throw new Error("Missing INFISICAL_PROJECT_ID/INFISICAL_ENV");
  }

  const client = new InfisicalSDK({
    siteUrl: siteUrl || undefined,
  });

  await client.auth().universalAuth.login({
    clientId,
    clientSecret,
  });

  const res = await client.secrets().listSecrets({
    projectId,
    environment,
    path,
  });

  const secretsList = res?.secrets ?? res ?? [];
  const map = {};

  for (const s of secretsList) {
    if (!s) continue;
    const key = s.secretKey ?? s.key;
    const value = s.secretValue ?? s.value;
    if (typeof key === "string" && typeof value === "string") {
      map[key] = value;
    }
  }

  return map;
}

