/*
 * Purpose: Validate payload structure and data integrity against JSON schemas
 * Created/Updated: 2025-11-20
 * Agent: BACKEND_AGENT
 * 
 * Usage in n8n Code node:
 *   const validationResult = validatePayload($input.item.json, 'contact');
 *   if (!validationResult.valid) {
 *     throw new Error(`Validation failed: ${validationResult.errors.join(', ')}`);
 *   }
 */

/**
 * Validates a payload against a JSON schema
 * @param {Object} payload - The payload to validate
 * @param {string} schemaType - Type of schema ('event', 'contact', 'incident', 'infra_deploy')
 * @param {Object} schema - Optional: Custom schema object (if not provided, uses built-in schemas)
 * @returns {Object} Validation result with 'valid' boolean and 'errors' array
 */
function validatePayload(payload, schemaType, schema = null) {
  const errors = [];
  
  // Basic type checks
  if (!payload || typeof payload !== 'object') {
    return {
      valid: false,
      errors: ['Payload must be an object']
    };
  }
  
  if (!schemaType || typeof schemaType !== 'string') {
    return {
      valid: false,
      errors: ['Schema type must be a string']
    };
  }
  
  // Use provided schema or get schema by type
  const validationSchema = schema || getSchemaByType(schemaType);
  
  if (!validationSchema) {
    return {
      valid: false,
      errors: [`Unknown schema type: ${schemaType}`]
    };
  }
  
  // Validate required fields
  if (validationSchema.required) {
    for (const field of validationSchema.required) {
      if (!(field in payload) || payload[field] === null || payload[field] === undefined) {
        errors.push(`Missing required field: ${field}`);
      }
    }
  }
  
  // Validate field types and constraints
  if (validationSchema.properties) {
    for (const [field, fieldSchema] of Object.entries(validationSchema.properties)) {
      if (field in payload) {
        const fieldErrors = validateField(payload[field], fieldSchema, field);
        errors.push(...fieldErrors);
      }
    }
  }
  
  // Check for additional properties if not allowed
  if (validationSchema.additionalProperties === false) {
    const allowedFields = new Set([
      ...(validationSchema.required || []),
      ...Object.keys(validationSchema.properties || {})
    ]);
    
    for (const field of Object.keys(payload)) {
      if (!allowedFields.has(field)) {
        errors.push(`Unexpected field: ${field}`);
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors: errors
  };
}

/**
 * Validates a single field against its schema definition
 * @param {*} value - The field value to validate
 * @param {Object} fieldSchema - Schema definition for the field
 * @param {string} fieldName - Name of the field (for error messages)
 * @returns {Array} Array of error messages (empty if valid)
 */
function validateField(value, fieldSchema, fieldName) {
  const errors = [];
  
  // Type validation
  if (fieldSchema.type) {
    const expectedTypes = Array.isArray(fieldSchema.type) 
      ? fieldSchema.type 
      : [fieldSchema.type];
    
    const actualType = getValueType(value);
    if (!expectedTypes.includes(actualType) && !expectedTypes.includes('null')) {
      errors.push(`${fieldName}: expected type ${expectedTypes.join(' or ')}, got ${actualType}`);
      return errors; // Skip further validation if type is wrong
    }
  }
  
  // String validations
  if (typeof value === 'string') {
    if (fieldSchema.minLength && value.length < fieldSchema.minLength) {
      errors.push(`${fieldName}: string length must be at least ${fieldSchema.minLength}`);
    }
    if (fieldSchema.maxLength && value.length > fieldSchema.maxLength) {
      errors.push(`${fieldName}: string length must be at most ${fieldSchema.maxLength}`);
    }
    if (fieldSchema.pattern) {
      const regex = new RegExp(fieldSchema.pattern);
      if (!regex.test(value)) {
        errors.push(`${fieldName}: string does not match required pattern`);
      }
    }
    if (fieldSchema.format === 'email' && !isValidEmail(value)) {
      errors.push(`${fieldName}: invalid email format`);
    }
    if (fieldSchema.format === 'date-time' && !isValidDateTime(value)) {
      errors.push(`${fieldName}: invalid date-time format (expected ISO 8601)`);
    }
  }
  
  // Number validations
  if (typeof value === 'number') {
    if (fieldSchema.minimum !== undefined && value < fieldSchema.minimum) {
      errors.push(`${fieldName}: value must be at least ${fieldSchema.minimum}`);
    }
    if (fieldSchema.maximum !== undefined && value > fieldSchema.maximum) {
      errors.push(`${fieldName}: value must be at most ${fieldSchema.maximum}`);
    }
  }
  
  // Enum validation
  if (fieldSchema.enum && !fieldSchema.enum.includes(value)) {
    errors.push(`${fieldName}: value must be one of: ${fieldSchema.enum.join(', ')}`);
  }
  
  // Array validation
  if (Array.isArray(value)) {
    if (fieldSchema.items) {
      value.forEach((item, index) => {
        const itemErrors = validateField(item, fieldSchema.items, `${fieldName}[${index}]`);
        errors.push(...itemErrors);
      });
    }
  }
  
  // Object validation
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    if (fieldSchema.properties) {
      for (const [subField, subSchema] of Object.entries(fieldSchema.properties)) {
        if (subField in value) {
          const subErrors = validateField(value[subField], subSchema, `${fieldName}.${subField}`);
          errors.push(...subErrors);
        }
      }
    }
  }
  
  return errors;
}

/**
 * Gets the JavaScript type of a value
 * @param {*} value - The value to check
 * @returns {string} Type name ('string', 'number', 'boolean', 'object', 'array', 'null')
 */
function getValueType(value) {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
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

/**
 * Validates ISO 8601 date-time format
 * @param {string} dateTime - Date-time string to validate
 * @returns {boolean} True if valid ISO 8601 format
 */
function isValidDateTime(dateTime) {
  const date = new Date(dateTime);
  return !isNaN(date.getTime()) && dateTime.includes('T');
}

/**
 * Gets schema definition by type
 * @param {string} schemaType - Schema type name
 * @returns {Object|null} Schema definition or null if not found
 */
function getSchemaByType(schemaType) {
  // Note: In n8n, you would load schemas from files or use inline definitions
  // This is a simplified version - in production, load from shared/schemas/
  
  const schemas = {
    'event': {
      required: ['id', 'type', 'source', 'env', 'timestamp', 'payload'],
      properties: {
        id: { type: 'string', pattern: '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' },
        type: { type: 'string' },
        source: { type: 'string', enum: ['n8n', 'backend', 'frontend', 'infra', 'github', 'external'] },
        env: { type: 'string', enum: ['dev', 'staging', 'prod'] },
        timestamp: { type: 'string', format: 'date-time' },
        correlation_id: { type: ['string', 'null'] },
        payload: { type: 'object' }
      },
      additionalProperties: false
    },
    'contact': {
      required: ['email'],
      properties: {
        email: { type: 'string', format: 'email', minLength: 1, maxLength: 255 },
        first_name: { type: ['string', 'null'], maxLength: 100 },
        last_name: { type: ['string', 'null'], maxLength: 100 },
        company: { type: ['string', 'null'], maxLength: 200 },
        phone: { type: ['string', 'null'] },
        status: { type: ['string', 'null'], enum: ['new', 'contacted', 'qualified', 'converted', 'lost', null] }
      },
      additionalProperties: false
    }
    // Add other schemas as needed
  };
  
  return schemas[schemaType] || null;
}

// Export for use in n8n Code nodes
module.exports = {
  validatePayload,
  validateField,
  getSchemaByType
};
