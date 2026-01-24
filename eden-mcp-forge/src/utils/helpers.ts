import { ToolDefinition, ServerConfig } from '../interfaces';

export function camelCase(str: string): string {
  return str.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
}

export function pascalCase(str: string): string {
  return str.replace(/(^|-)([a-z])/g, (g) => g.slice(-1).toUpperCase());
}

export function kebabCase(str: string): string {
  return str.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
}

export function validateToolName(name: string): { valid: boolean; error?: string } {
  if (!name.match(/^[a-z][a-z0-9-]*$/)) {
    return {
      valid: false,
      error: 'Tool name must start with a lowercase letter and contain only lowercase letters, numbers, and hyphens'
    };
  }

  if (name.length > 50) {
    return {
      valid: false,
      error: 'Tool name must be 50 characters or less'
    };
  }

  return { valid: true };
}

export function validateHandlerCode(code: string): { valid: boolean; error?: string } {
  try {
    // Basic syntax check using Function constructor
    new Function(code);
    return { valid: true };
  } catch (error) {
    return {
      valid: false,
      error: `Invalid JavaScript syntax: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

export function generateSafetyChecks(safety: any, tool: ToolDefinition): string[] {
  const checks: string[] = [];

  if (safety.requireUserApproval) {
    checks.push('// User approval required for this operation');
  }

  if (safety.restrictedParameters.length > 0) {
    const restrictedInTool = safety.restrictedParameters.filter((param: string) =>
      Object.keys(tool.parameters || {}).includes(param)
    );
    if (restrictedInTool.length > 0) {
      checks.push(`// Restricted parameters detected: ${restrictedInTool.join(', ')}`);
    }
  }

  if (tool.annotations?.destructiveHint) {
    checks.push('// DESTRUCTIVE OPERATION: This tool may make irreversible changes');
  }

  if (tool.annotations?.openWorldHint) {
    checks.push('// EXTERNAL API: This tool interacts with external systems');
  }

  return checks;
}

export function generateParameterSchema(parameters: Record<string, any>): string {
  const schema: string[] = [];

  for (const [key, config] of Object.entries(parameters)) {
    const type = config.type || 'string';
    const description = config.description || '';
    const required = config.required !== false;

    let paramLine = `  ${key}: z.${type}()`;

    if (description) {
      paramLine += `.describe('${description}')`;
    }

    if (!required) {
      paramLine += '.optional()';
    }

    if (config.default !== undefined) {
      paramLine += `.default(${JSON.stringify(config.default)})`;
    }

    schema.push(paramLine);
  }

  return schema.join(',\n');
}

export function sanitizeHandlerCode(code: string): string {
  // Remove potential malicious code patterns
  const dangerousPatterns = [
    /eval\s*\(/gi,
    /Function\s*\(/gi,
    /setTimeout\s*\(/gi,
    /setInterval\s*\(/gi,
    /process\.exit/gi,
    /require\s*\(\s*['"`]fs['"`]\s*\)/gi,
  ];

  let sanitized = code;

  for (const pattern of dangerousPatterns) {
    if (pattern.test(sanitized)) {
      throw new Error('Potentially dangerous code detected in handler');
    }
  }

  return sanitized;
}
