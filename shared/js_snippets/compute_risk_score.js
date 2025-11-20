/*
 * Purpose: Compute risk score based on input parameters for contact/lead risk assessment
 * Created/Updated: 2025-11-20
 * Agent: BACKEND_AGENT
 * 
 * Usage in n8n Code node:
 *   const riskScore = computeRiskScore($input.item.json);
 *   return { ...$input.item.json, metadata: { risk_score: riskScore } };
 */

/**
 * Computes a risk score (0-100) for a contact based on various factors
 * @param {Object} contact - Contact data object (normalized contact preferred)
 * @param {Object} options - Optional configuration for risk calculation
 * @returns {number} Risk score from 0 (low risk) to 100 (high risk)
 */
function computeRiskScore(contact, options = {}) {
  if (!contact || typeof contact !== 'object') {
    throw new Error('Contact data must be an object');
  }
  
  const config = {
    emailDomainWeight: options.emailDomainWeight || 20,
    emailFormatWeight: options.emailFormatWeight || 15,
    phoneWeight: options.phoneWeight || 15,
    companyWeight: options.companyWeight || 10,
    sourceWeight: options.sourceWeight || 10,
    statusWeight: options.statusWeight || 10,
    dataCompletenessWeight: options.dataCompletenessWeight || 20,
    ...options
  };
  
  let riskScore = 0;
  
  // Email domain risk (suspicious domains increase risk)
  riskScore += calculateEmailDomainRisk(contact.email, config.emailDomainWeight);
  
  // Email format risk (invalid or suspicious formats)
  riskScore += calculateEmailFormatRisk(contact.email, config.emailFormatWeight);
  
  // Phone number risk (missing or invalid phone)
  riskScore += calculatePhoneRisk(contact.phone, config.phoneWeight);
  
  // Company information risk (missing company data)
  riskScore += calculateCompanyRisk(contact.company, config.companyWeight);
  
  // Source risk (unknown or suspicious sources)
  riskScore += calculateSourceRisk(contact.source, config.sourceWeight);
  
  // Status risk (lost or low-value statuses)
  riskScore += calculateStatusRisk(contact.status, config.statusWeight);
  
  // Data completeness risk (missing required fields)
  riskScore += calculateDataCompletenessRisk(contact, config.dataCompletenessWeight);
  
  // Ensure score is between 0 and 100
  return Math.max(0, Math.min(100, Math.round(riskScore)));
}

/**
 * Calculates risk based on email domain
 * @param {string} email - Email address
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateEmailDomainRisk(email, maxWeight) {
  if (!email || typeof email !== 'string') {
    return maxWeight; // Missing email is high risk
  }
  
  const domain = email.split('@')[1];
  if (!domain) {
    return maxWeight;
  }
  
  // High-risk domains (disposable email services, etc.)
  const highRiskDomains = [
    'tempmail.com', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'throwaway.email', 'temp-mail.org'
  ];
  
  if (highRiskDomains.some(riskDomain => domain.toLowerCase().includes(riskDomain))) {
    return maxWeight;
  }
  
  // Low-risk domains (known good providers)
  const lowRiskDomains = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
    'icloud.com', 'protonmail.com', 'aol.com'
  ];
  
  if (lowRiskDomains.includes(domain.toLowerCase())) {
    return maxWeight * 0.1; // Low risk for known providers
  }
  
  // Corporate domains (usually lower risk)
  if (domain.includes('.') && !domain.includes('..')) {
    return maxWeight * 0.3;
  }
  
  return maxWeight * 0.5; // Medium risk for unknown domains
}

/**
 * Calculates risk based on email format
 * @param {string} email - Email address
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateEmailFormatRisk(email, maxWeight) {
  if (!email || typeof email !== 'string') {
    return maxWeight;
  }
  
  // Invalid email format
  if (!isValidEmail(email)) {
    return maxWeight;
  }
  
  // Suspicious patterns
  const suspiciousPatterns = [
    /^[0-9]+@/,  // Starts with numbers
    /test@/i,    // Contains "test"
    /fake@/i,    // Contains "fake"
    /spam@/i,    // Contains "spam"
    /temp@/i     // Contains "temp"
  ];
  
  for (const pattern of suspiciousPatterns) {
    if (pattern.test(email)) {
      return maxWeight * 0.8;
    }
  }
  
  return 0; // Valid email format
}

/**
 * Calculates risk based on phone number
 * @param {string} phone - Phone number
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculatePhoneRisk(phone, maxWeight) {
  if (!phone || phone === null || phone === undefined) {
    return maxWeight * 0.7; // Missing phone is medium-high risk
  }
  
  const phoneStr = String(phone).trim();
  
  // Invalid phone format
  if (phoneStr.length < 10) {
    return maxWeight * 0.8;
  }
  
  // All same digits (suspicious)
  if (/^(\d)\1+$/.test(phoneStr.replace(/\D/g, ''))) {
    return maxWeight * 0.6;
  }
  
  return 0; // Valid phone
}

/**
 * Calculates risk based on company information
 * @param {string} company - Company name
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateCompanyRisk(company, maxWeight) {
  if (!company || company === null || company === undefined || company.trim() === '') {
    return maxWeight * 0.5; // Missing company is medium risk
  }
  
  const companyStr = String(company).trim().toLowerCase();
  
  // Suspicious company names
  const suspiciousCompanies = ['test', 'fake', 'spam', 'temp', 'unknown', 'n/a', 'na'];
  if (suspiciousCompanies.includes(companyStr)) {
    return maxWeight * 0.7;
  }
  
  return 0; // Valid company
}

/**
 * Calculates risk based on lead source
 * @param {string} source - Lead source
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateSourceRisk(source, maxWeight) {
  if (!source || source === null || source === undefined) {
    return maxWeight * 0.4; // Unknown source is medium risk
  }
  
  const sourceStr = String(source).trim().toLowerCase();
  
  // High-risk sources
  const highRiskSources = ['spam', 'unknown', 'test', 'fake'];
  if (highRiskSources.includes(sourceStr)) {
    return maxWeight * 0.8;
  }
  
  // Low-risk sources (known good sources)
  const lowRiskSources = ['website', 'referral', 'event', 'partner', 'organic'];
  if (lowRiskSources.includes(sourceStr)) {
    return 0;
  }
  
  return maxWeight * 0.3; // Unknown source is medium risk
}

/**
 * Calculates risk based on contact status
 * @param {string} status - Contact status
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateStatusRisk(status, maxWeight) {
  if (!status || status === null || status === undefined) {
    return 0; // No status is neutral
  }
  
  const statusStr = String(status).trim().toLowerCase();
  
  // High-risk statuses
  if (statusStr === 'lost') {
    return maxWeight * 0.6;
  }
  
  // Low-risk statuses
  if (['qualified', 'converted'].includes(statusStr)) {
    return 0;
  }
  
  return 0; // Other statuses are neutral
}

/**
 * Calculates risk based on data completeness
 * @param {Object} contact - Contact data
 * @param {number} maxWeight - Maximum weight for this factor
 * @returns {number} Risk score contribution
 */
function calculateDataCompletenessRisk(contact, maxWeight) {
  const requiredFields = ['email'];
  const importantFields = ['first_name', 'last_name', 'company', 'phone'];
  
  let missingRequired = 0;
  let missingImportant = 0;
  
  // Check required fields
  for (const field of requiredFields) {
    if (!contact[field] || contact[field] === null || contact[field] === undefined) {
      missingRequired++;
    }
  }
  
  // Check important fields
  for (const field of importantFields) {
    if (!contact[field] || contact[field] === null || contact[field] === undefined) {
      missingImportant++;
    }
  }
  
  // Calculate risk based on missing fields
  const requiredRisk = (missingRequired / requiredFields.length) * maxWeight * 0.6;
  const importantRisk = (missingImportant / importantFields.length) * maxWeight * 0.4;
  
  return requiredRisk + importantRisk;
}

/**
 * Validates email format
 * @param {string} email - Email address to validate
 * @returns {boolean} True if valid email format
 */
function isValidEmail(email) {
  if (!email || typeof email !== 'string') {
    return false;
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Export for use in n8n Code nodes
module.exports = {
  computeRiskScore,
  calculateEmailDomainRisk,
  calculateEmailFormatRisk,
  calculatePhoneRisk,
  calculateCompanyRisk,
  calculateSourceRisk,
  calculateStatusRisk,
  calculateDataCompletenessRisk
};
