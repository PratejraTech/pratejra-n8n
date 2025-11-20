/*
 * Purpose: Normalize contact data structure for consistent processing across workflows
 * Created/Updated: 2025-11-20
 * Agent: BACKEND_AGENT
 * 
 * Usage in n8n Code node:
 *   const normalized = normalizeContact($input.item.json);
 *   return normalized;
 */

/**
 * Normalizes contact data to ensure consistent structure and format
 * @param {Object} contact - Raw contact data from various sources
 * @returns {Object} Normalized contact object conforming to contact.schema.json
 */
function normalizeContact(contact) {
  if (!contact || typeof contact !== 'object') {
    throw new Error('Contact data must be an object');
  }
  
  const normalized = {
    email: normalizeEmail(contact.email || contact.Email || contact.email_address || ''),
    first_name: normalizeString(contact.first_name || contact.firstName || contact.first || contact['First Name'] || null),
    last_name: normalizeString(contact.last_name || contact.lastName || contact.last || contact['Last Name'] || null),
    company: normalizeString(contact.company || contact.Company || contact.organization || contact.Organization || null),
    phone: normalizePhone(contact.phone || contact.Phone || contact.phone_number || contact.phoneNumber || null),
    title: normalizeString(contact.title || contact.Title || contact.job_title || contact.jobTitle || null),
    source: normalizeString(contact.source || contact.Source || contact.lead_source || contact.leadSource || null),
    status: normalizeStatus(contact.status || contact.Status || contact.lead_status || contact.leadStatus || null),
    tags: normalizeTags(contact.tags || contact.Tags || contact.tag || []),
    custom_fields: extractCustomFields(contact),
    created_at: normalizeDateTime(contact.created_at || contact.createdAt || contact['Created At'] || contact.created || null),
    updated_at: normalizeDateTime(contact.updated_at || contact.updatedAt || contact['Updated At'] || contact.updated || null),
    metadata: normalizeMetadata(contact)
  };
  
  // Add ID if present
  if (contact.id || contact.Id || contact.ID) {
    normalized.id = normalizeUUID(contact.id || contact.Id || contact.ID);
  }
  
  return normalized;
}

/**
 * Normalizes email address
 * @param {string} email - Email address
 * @returns {string} Normalized email (lowercase, trimmed)
 */
function normalizeEmail(email) {
  if (!email || typeof email !== 'string') {
    throw new Error('Email is required and must be a string');
  }
  
  const normalized = email.trim().toLowerCase();
  
  // Basic email validation
  if (!isValidEmail(normalized)) {
    throw new Error(`Invalid email format: ${email}`);
  }
  
  return normalized;
}

/**
 * Normalizes string fields (trims, handles null/undefined)
 * @param {*} value - String value to normalize
 * @param {number} maxLength - Maximum length (optional)
 * @returns {string|null} Normalized string or null
 */
function normalizeString(value, maxLength = null) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  
  const normalized = String(value).trim();
  
  if (normalized === '') {
    return null;
  }
  
  if (maxLength && normalized.length > maxLength) {
    return normalized.substring(0, maxLength);
  }
  
  return normalized;
}

/**
 * Normalizes phone number
 * @param {*} phone - Phone number
 * @returns {string|null} Normalized phone number or null
 */
function normalizePhone(phone) {
  if (!phone || phone === null || phone === undefined) {
    return null;
  }
  
  // Remove common formatting characters
  let normalized = String(phone).replace(/[\s\-\(\)\.]/g, '');
  
  // Add + prefix if missing and number doesn't start with it
  if (!normalized.startsWith('+')) {
    // Assume US number if starts with 1, otherwise add +1
    if (normalized.startsWith('1') && normalized.length === 11) {
      normalized = '+' + normalized;
    } else if (normalized.length === 10) {
      normalized = '+1' + normalized; // Default to US
    }
  }
  
  return normalized || null;
}

/**
 * Normalizes contact status
 * @param {*} status - Status value
 * @returns {string|null} Normalized status or null
 */
function normalizeStatus(status) {
  if (!status || status === null || status === undefined) {
    return null;
  }
  
  const statusMap = {
    'new': 'new',
    'New': 'new',
    'NEW': 'new',
    'contacted': 'contacted',
    'Contacted': 'contacted',
    'CONTACTED': 'contacted',
    'qualified': 'qualified',
    'Qualified': 'qualified',
    'QUALIFIED': 'qualified',
    'converted': 'converted',
    'Converted': 'converted',
    'CONVERTED': 'converted',
    'lost': 'lost',
    'Lost': 'lost',
    'LOST': 'lost'
  };
  
  const normalized = String(status).toLowerCase().trim();
  return statusMap[normalized] || normalized || null;
}

/**
 * Normalizes tags array
 * @param {*} tags - Tags value (can be array, string, or comma-separated string)
 * @returns {Array} Array of normalized tag strings
 */
function normalizeTags(tags) {
  if (!tags) {
    return [];
  }
  
  if (Array.isArray(tags)) {
    return tags
      .map(tag => normalizeString(tag, 50))
      .filter(tag => tag !== null && tag !== '');
  }
  
  if (typeof tags === 'string') {
    // Handle comma-separated tags
    return tags
      .split(',')
      .map(tag => normalizeString(tag, 50))
      .filter(tag => tag !== null && tag !== '');
  }
  
  return [];
}

/**
 * Extracts custom fields from contact data
 * @param {Object} contact - Raw contact data
 * @returns {Object} Custom fields object
 */
function extractCustomFields(contact) {
  const standardFields = [
    'id', 'Id', 'ID', 'email', 'Email', 'email_address', 'emailAddress',
    'first_name', 'firstName', 'first', 'First Name',
    'last_name', 'lastName', 'last', 'Last Name',
    'company', 'Company', 'organization', 'Organization',
    'phone', 'Phone', 'phone_number', 'phoneNumber',
    'title', 'Title', 'job_title', 'jobTitle',
    'source', 'Source', 'lead_source', 'leadSource',
    'status', 'Status', 'lead_status', 'leadStatus',
    'tags', 'Tags', 'tag',
    'created_at', 'createdAt', 'Created At', 'created',
    'updated_at', 'updatedAt', 'Updated At', 'updated',
    'metadata', 'Metadata'
  ];
  
  const customFields = {};
  
  for (const [key, value] of Object.entries(contact)) {
    if (!standardFields.includes(key) && value !== null && value !== undefined) {
      customFields[key] = value;
    }
  }
  
  return Object.keys(customFields).length > 0 ? customFields : {};
}

/**
 * Normalizes date-time strings to ISO 8601 format
 * @param {*} dateTime - Date-time value
 * @returns {string|null} ISO 8601 formatted date-time or null
 */
function normalizeDateTime(dateTime) {
  if (!dateTime || dateTime === null || dateTime === undefined) {
    return null;
  }
  
  try {
    const date = new Date(dateTime);
    if (isNaN(date.getTime())) {
      return null;
    }
    return date.toISOString();
  } catch (error) {
    return null;
  }
}

/**
 * Normalizes UUID format
 * @param {*} uuid - UUID value
 * @returns {string|null} Normalized UUID or null
 */
function normalizeUUID(uuid) {
  if (!uuid || uuid === null || uuid === undefined) {
    return null;
  }
  
  const normalized = String(uuid).trim().toLowerCase();
  
  // Basic UUID format validation
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  if (!uuidRegex.test(normalized)) {
    return null; // Invalid UUID format
  }
  
  return normalized;
}

/**
 * Normalizes metadata object
 * @param {Object} contact - Raw contact data
 * @returns {Object} Normalized metadata object
 */
function normalizeMetadata(contact) {
  const metadata = {};
  
  // Risk score
  if (contact.risk_score !== undefined || contact.riskScore !== undefined) {
    const riskScore = contact.risk_score || contact.riskScore;
    if (typeof riskScore === 'number' && riskScore >= 0 && riskScore <= 100) {
      metadata.risk_score = riskScore;
    }
  }
  
  // Enrichment status
  if (contact.enrichment_status || contact.enrichmentStatus) {
    const status = String(contact.enrichment_status || contact.enrichmentStatus).toLowerCase();
    if (['pending', 'in_progress', 'completed', 'failed'].includes(status)) {
      metadata.enrichment_status = status;
    }
  }
  
  // Last enriched at
  if (contact.last_enriched_at || contact.lastEnrichedAt) {
    metadata.last_enriched_at = normalizeDateTime(contact.last_enriched_at || contact.lastEnrichedAt);
  }
  
  return Object.keys(metadata).length > 0 ? metadata : {};
}

/**
 * Validates email format
 * @param {string} email - Email address to validate
 * @returns {boolean} True if valid email format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Export for use in n8n Code nodes
module.exports = {
  normalizeContact,
  normalizeEmail,
  normalizeString,
  normalizePhone,
  normalizeStatus,
  normalizeTags,
  extractCustomFields,
  normalizeDateTime,
  normalizeUUID,
  normalizeMetadata
};
