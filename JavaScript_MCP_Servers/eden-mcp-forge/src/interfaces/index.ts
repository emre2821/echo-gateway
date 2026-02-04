import { z } from 'zod';

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, any>;
  annotations?: {
    title?: string;
    readOnlyHint?: boolean;
    destructiveHint?: boolean;
    idempotentHint?: boolean;
    openWorldHint?: boolean;
  };
  handler: string;
}

export interface ServerConfig {
  name: string;
  version: string;
  description: string;
  author?: string;
  license?: string;
  tools: ToolDefinition[];
  resources?: ResourceDefinition[];
  prompts?: PromptDefinition[];
}

export interface ResourceDefinition {
  uri: string;
  name: string;
  description: string;
  mimeType?: string;
}

export interface PromptDefinition {
  name: string;
  description: string;
  arguments?: Record<string, any>;
}

export interface SafetyConfig {
  requireUserApproval: boolean;
  allowedOperations: string[];
  restrictedParameters: string[];
  maxExecutionTime?: number;
  enableLogging: boolean;
}

export interface GeneratorConfig {
  server: ServerConfig;
  safety: SafetyConfig;
  output: {
    directory: string;
    packageManager: 'npm' | 'yarn' | 'pnpm';
    includeTests: boolean;
    includeDocs: boolean;
  };
}

export const ToolDefinitionSchema = z.object({
  name: z.string().min(1).describe('Tool name (kebab-case)'),
  description: z.string().min(1).describe('Tool description'),
  parameters: z.record(z.any()).describe('Tool parameters schema'),
  annotations: z.object({
    title: z.string().optional(),
    readOnlyHint: z.boolean().optional(),
    destructiveHint: z.boolean().optional(),
    idempotentHint: z.boolean().optional(),
    openWorldHint: z.boolean().optional(),
  }).optional(),
  handler: z.string().min(1).describe('Handler implementation code'),
});

export const ServerConfigSchema = z.object({
  name: z.string().min(1).describe('Server name'),
  version: z.string().min(1).describe('Server version'),
  description: z.string().min(1).describe('Server description'),
  author: z.string().optional(),
  license: z.string().optional(),
  tools: z.array(ToolDefinitionSchema).min(1).describe('At least one tool is required'),
  resources: z.array(z.any()).optional(),
  prompts: z.array(z.any()).optional(),
});

export const SafetyConfigSchema = z.object({
  requireUserApproval: z.boolean().default(true).describe('Require user approval for tool execution'),
  allowedOperations: z.array(z.string()).default([]).describe('Allowed operation types'),
  restrictedParameters: z.array(z.string()).default([]).describe('Restricted parameter names'),
  maxExecutionTime: z.number().optional().describe('Maximum execution time in seconds'),
  enableLogging: z.boolean().default(true).describe('Enable execution logging'),
});

export const GeneratorConfigSchema = z.object({
  server: ServerConfigSchema,
  safety: SafetyConfigSchema,
  output: z.object({
    directory: z.string().default('./mcp-server-output').describe('Output directory'),
    packageManager: z.enum(['npm', 'yarn', 'pnpm']).default('npm').describe('Package manager to use'),
    includeTests: z.boolean().default(true).describe('Include test files'),
    includeDocs: z.boolean().default(true).describe('Include documentation'),
  }),
});

export type ValidatedConfig = z.infer<typeof GeneratorConfigSchema>;
