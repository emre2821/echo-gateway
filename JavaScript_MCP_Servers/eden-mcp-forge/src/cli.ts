#!/usr/bin/env node

import chalk from 'chalk';
import inquirer from 'inquirer';
import * as fs from 'fs-extra';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import Handlebars from 'handlebars';
import {
  GeneratorConfigSchema,
  ValidatedConfig,
  ToolDefinition,
  ServerConfig
} from './interfaces/index.js';
import {
  validateToolName,
  validateHandlerCode,
  generateSafetyChecks,
  sanitizeHandlerCode,
  camelCase,
  pascalCase,
  kebabCase
} from './utils/helpers.js';

// Get current directory for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Register Handlebars helpers
Handlebars.registerHelper('camelCase', camelCase);
Handlebars.registerHelper('pascalCase', pascalCase);
Handlebars.registerHelper('kebabCase', kebabCase);

class MCPServerCreator {
  private config: Partial<ValidatedConfig> = {};

  async run(): Promise<void> {
    console.log(chalk.blue.bold('🚀 MCP Server Creator'));
    console.log(chalk.gray('Create custom MCP servers with safety and human-in-the-loop permissions\n'));

    try {
      await this.collectServerInfo();
      await this.collectTools();
      await this.collectSafetyConfig();
      await this.collectOutputConfig();

      const validatedConfig = GeneratorConfigSchema.parse(this.config);

      await this.generateServer(validatedConfig);

      console.log(chalk.green.bold('\n✅ MCP Server created successfully!'));
      console.log(chalk.gray(`Check the output directory: ${validatedConfig.output.directory}`));

    } catch (error) {
      console.error(chalk.red('❌ Error:', error instanceof Error ? error.message : 'Unknown error'));
      process.exit(1);
    }
  }

  private async collectServerInfo(): Promise<void> {
    console.log(chalk.yellow('📋 Server Information'));

    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Server name (kebab-case):',
        validate: (input: string) => {
          if (!input.trim()) return 'Server name is required';
          if (!input.match(/^[a-z][a-z0-9-]*$/)) {
            return 'Must start with lowercase letter and contain only lowercase letters, numbers, and hyphens';
          }
          return true;
        }
      },
      {
        type: 'input',
        name: 'version',
        message: 'Server version:',
        default: '1.0.0',
        validate: (input: string) => {
          if (!input.trim()) return 'Version is required';
          if (!input.match(/^\d+\.\d+\.\d+$/)) {
            return 'Must be in format x.y.z (e.g., 1.0.0)';
          }
          return true;
        }
      },
      {
        type: 'input',
        name: 'description',
        message: 'Server description:',
        validate: (input: string) => input.trim().length > 0 || 'Description is required'
      },
      {
        type: 'input',
        name: 'author',
        message: 'Author (optional):'
      },
      {
        type: 'input',
        name: 'license',
        message: 'License (optional):',
        default: 'MIT'
      }
    ]);

    this.config.server = {
      ...this.config.server,
      ...answers,
      tools: []
    };
  }

  private async collectTools(): Promise<void> {
    console.log(chalk.yellow('\n🛠️  Tools Configuration'));

    const tools: ToolDefinition[] = [];
    let addMore = true;

    while (addMore) {
      const tool = await this.collectSingleTool(tools.length + 1);

      if (tool) {
        tools.push(tool);
        console.log(chalk.green(`✓ Tool "${tool.name}" added`));
      }

      const { continue: shouldContinue } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'continue',
          message: 'Add another tool?',
          default: false
        }
      ]);

      addMore = shouldContinue;
    }

    this.config.server!.tools = tools;
  }

  private async collectSingleTool(toolNumber: number): Promise<ToolDefinition | null> {
    console.log(chalk.cyan(`\n--- Tool ${toolNumber} ---`));

    const basicInfo = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Tool name (kebab-case):',
        validate: (input: string) => {
          const validation = validateToolName(input);
          return validation.valid || validation.error;
        }
      },
      {
        type: 'input',
        name: 'description',
        message: 'Tool description:',
        validate: (input: string) => input.trim().length > 0 || 'Description is required'
      }
    ]);

    // Collect parameters
    const parameters = await this.collectParameters();

    // Collect annotations
    const annotations = await this.collectAnnotations();

    // Collect handler code
    const handlerCode = await this.collectHandlerCode(basicInfo.name);

    return {
      ...basicInfo,
      parameters,
      annotations,
      handler: handlerCode
    };
  }

  private async collectParameters(): Promise<Record<string, any>> {
    const parameters: Record<string, any> = {};
    let addMore = false;

    const { hasParameters } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'hasParameters',
        message: 'Does this tool have parameters?',
        default: true
      }
    ]);

    if (!hasParameters) return parameters;

    do {
      const param = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Parameter name (camelCase):',
          validate: (input: string) => {
            if (!input.match(/^[a-z][a-zA-Z0-9]*$/)) {
              return 'Must start with lowercase letter and be camelCase';
            }
            return true;
          }
        },
        {
          type: 'list',
          name: 'type',
          message: 'Parameter type:',
          choices: ['string', 'number', 'boolean', 'array', 'object'],
          default: 'string'
        },
        {
          type: 'input',
          name: 'description',
          message: 'Parameter description:',
          validate: (input: string) => input.trim().length > 0 || 'Description is required'
        },
        {
          type: 'confirm',
          name: 'required',
          message: 'Is this parameter required?',
          default: true
        }
      ]);

      parameters[param.name] = {
        type: param.type,
        description: param.description,
        required: param.required
      };

      const { addParam } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'addParam',
          message: 'Add another parameter?',
          default: false
        }
      ]);

      addMore = addParam;
    } while (addMore);

    return parameters;
  }

  private async collectAnnotations(): Promise<any> {
    const { useAnnotations } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'useAnnotations',
        message: 'Add safety annotations for this tool?',
        default: true
      }
    ]);

    if (!useAnnotations) return undefined;

    return await inquirer.prompt([
      {
        type: 'input',
        name: 'title',
        message: 'Title (human-readable name):'
      },
      {
        type: 'confirm',
        name: 'readOnlyHint',
        message: 'Read-only operation (does not modify state)?',
        default: false
      },
      {
        type: 'confirm',
        name: 'destructiveHint',
        message: 'Destructive operation (may make irreversible changes)?',
        default: false
      },
      {
        type: 'confirm',
        name: 'idempotentHint',
        message: 'Idempotent operation (same result when called multiple times)?',
        default: false
      },
      {
        type: 'confirm',
        name: 'openWorldHint',
        message: 'Interacts with external systems/APIs?',
        default: false
      }
    ]);
  }

  private async collectHandlerCode(toolName: string): Promise<string> {
    console.log(chalk.cyan(`\n📝 Handler Implementation for ${toolName}`));
    console.log(chalk.gray('You will write the actual implementation code for your tool.'));
    console.log(chalk.gray('Available variables:'));
    console.log(chalk.gray('- Parameters are available as destructured variables'));
    console.log(chalk.gray('- Return value should be: { content: [{ type: "text", text: "result" }] }'));
    console.log(chalk.gray('- For errors: { content: [{ type: "text", text: "error" }], isError: true }'));

    const { handlerMethod } = await inquirer.prompt([
      {
        type: 'editor',
        name: 'handlerMethod',
        message: 'Write your handler implementation:',
        default: `// Example implementation
const result = \`Tool ${toolName} executed with parameters: \${JSON.stringify(args)}\`;
return {
  content: [{ type: 'text', text: result }]
};`
      }
    ]);

    const validation = validateHandlerCode(handlerMethod);
    if (!validation.valid) {
      console.error(chalk.red('❌ Invalid handler code:'), validation.error);
      return await this.collectHandlerCode(toolName);
    }

    try {
      return sanitizeHandlerCode(handlerMethod);
    } catch (error) {
      console.error(chalk.red('❌ Unsafe code detected:'), error instanceof Error ? error.message : 'Unknown error');
      return await this.collectHandlerCode(toolName);
    }
  }

  private async collectSafetyConfig(): Promise<void> {
    console.log(chalk.yellow('\n🔒 Safety Configuration'));

    const safetyConfig = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'requireUserApproval',
        message: 'Require user approval for tool execution?',
        default: true
      },
      {
        type: 'checkbox',
        name: 'allowedOperations',
        message: 'Allowed operation types:',
        choices: [
          { name: 'File operations', value: 'file' },
          { name: 'Network requests', value: 'network' },
          { name: 'System commands', value: 'system' },
          { name: 'Database operations', value: 'database' }
        ]
      },
      {
        type: 'input',
        name: 'restrictedParameters',
        message: 'Restricted parameter names (comma-separated):',
        default: 'password,token,secret,key'
      },
      {
        type: 'number',
        name: 'maxExecutionTime',
        message: 'Maximum execution time (seconds, 0 for unlimited):',
        default: 30,
        validate: (input: number) => input >= 0 || 'Must be 0 or positive'
      },
      {
        type: 'confirm',
        name: 'enableLogging',
        message: 'Enable execution logging?',
        default: true
      }
    ]);

    // Process restricted parameters
    if (typeof safetyConfig.restrictedParameters === 'string') {
      safetyConfig.restrictedParameters = safetyConfig.restrictedParameters
        .split(',')
        .map((p: string) => p.trim())
        .filter((p: string) => p.length > 0);
    }

    this.config.safety = safetyConfig;
  }

  private async collectOutputConfig(): Promise<void> {
    console.log(chalk.yellow('\n📁 Output Configuration'));

    const outputConfig = await inquirer.prompt([
      {
        type: 'input',
        name: 'directory',
        message: 'Output directory:',
        default: './mcp-server-output',
        validate: (input: string) => input.trim().length > 0 || 'Directory is required'
      },
      {
        type: 'list',
        name: 'packageManager',
        message: 'Package manager:',
        choices: ['npm', 'yarn', 'pnpm'],
        default: 'npm'
      },
      {
        type: 'confirm',
        name: 'includeTests',
        message: 'Include test files?',
        default: true
      },
      {
        type: 'confirm',
        name: 'includeDocs',
        message: 'Include documentation?',
        default: true
      }
    ]);

    this.config.output = outputConfig;
  }

  private async generateServer(config: ValidatedConfig): Promise<void> {
    const outputDir = path.resolve(config.output.directory);
    const serverName = config.server.name;

    // Create output directory
    await fs.ensureDir(outputDir);
    await fs.ensureDir(path.join(outputDir, 'src'));

    // Generate package.json
    const packageTemplate = await fs.readFile(
      path.join(__dirname, 'templates', 'package-template.hbs'),
      'utf8'
    );
    const packageContent = Handlebars.compile(packageTemplate)(config);
    await fs.writeFile(
      path.join(outputDir, 'package.json'),
      packageContent
    );

    // Generate main server file
    const serverTemplate = await fs.readFile(
      path.join(__dirname, 'templates', 'server-template.hbs'),
      'utf8'
    );
    const serverContent = Handlebars.compile(serverTemplate)(config);
    await fs.writeFile(
      path.join(outputDir, 'src', 'index.ts'),
      serverContent
    );

    // Generate tsconfig.json
    const tsconfig = {
      compilerOptions: {
        target: 'ES2020',
        module: 'commonjs',
        lib: ['ES2020'],
        outDir: './dist',
        rootDir: './src',
        strict: true,
        esModuleInterop: true,
        skipLibCheck: true,
        forceConsistentCasingInFileNames: true
      },
      include: ['src/**/*'],
      exclude: ['node_modules', 'dist']
    };
    await fs.writeFile(
      path.join(outputDir, 'tsconfig.json'),
      JSON.stringify(tsconfig, null, 2)
    );

    // Generate README
    if (config.output.includeDocs) {
      await this.generateReadme(config, outputDir);
    }

    // Generate tests
    if (config.output.includeTests) {
      await this.generateTests(config, outputDir);
    }

    // Show safety summary
    this.displaySafetySummary(config);
  }

  private async generateReadme(config: ValidatedConfig, outputDir: string): Promise<void> {
    const readme = `# ${config.server.name}

${config.server.description}

## Installation

\`\`\`bash
${config.output.packageManager} install
${config.output.packageManager} run build
\`\`\`

## Usage

\`\`\`bash
${config.output.packageManager} start
\`\`\`

## Tools

${config.server.tools.map(tool =>
  `### ${tool.name}\n\n${tool.description}\n\n${tool.parameters ?
    '**Parameters:**\n' + Object.entries(tool.parameters).map(([key, param]) =>
      `- \`${key}\` (${param.type}): ${param.description}${param.required ? ' (required)' : ' (optional)'}`
    ).join('\n') :
    'No parameters.'
  }`
).join('\n\n')}

## Safety Features

This MCP server includes the following safety features:

- ${config.safety.requireUserApproval ? '✅ User approval required for tool execution' : '❌ No user approval required'}
- ${config.safety.enableLogging ? '✅ Execution logging enabled' : '❌ Execution logging disabled'}
- Maximum execution time: ${config.safety.maxExecutionTime || 'Unlimited'} seconds
- Restricted parameters: ${config.safety.restrictedParameters.join(', ') || 'None'}

## License

${config.server.license || 'MIT'}
`;

    await fs.writeFile(path.join(outputDir, 'README.md'), readme);
  }

  private async generateTests(config: ValidatedConfig, outputDir: string): Promise<void> {
    await fs.ensureDir(path.join(outputDir, 'tests'));

    const testContent = `import { ${pascalCase(config.server.name)}Server } from '../src/index';

describe('${config.server.name}', () => {
  let server: ${pascalCase(config.server.name)}Server;

  beforeEach(() => {
    server = new ${pascalCase(config.server.name)}Server();
  });

  ${config.server.tools.map(tool =>
    `describe('${tool.name}', () => {
      it('should have correct tool definition', async () => {
        const tools = await server.listTools();
        const toolDef = tools.find(t => t.name === '${tool.name}');

        expect(toolDef).toBeDefined();
        expect(toolDef?.name).toBe('${tool.name}');
        expect(toolDef?.description).toBe('${tool.description}');
      });

      it('should validate parameters correctly', async () => {
        // Add parameter validation tests here
        const validArgs = { ${Object.keys(tool.parameters).map(key => `${key}: 'test'`).join(', ')} };

        // Test should not throw for valid args
        expect(() => server.validateParameters('${tool.name}', validArgs)).not.toThrow();
      });
    })`
  ).join('\n\n')}
});
`;

    await fs.writeFile(path.join(outputDir, 'tests', 'server.test.ts'), testContent);
  }

  private displaySafetySummary(config: ValidatedConfig): void {
    console.log(chalk.yellow('\n🔒 Safety Summary:'));

    config.server.tools.forEach((tool: ToolDefinition) => {
        const checks = generateSafetyChecks(config.safety!, tool);
      if (checks.length > 0) {
        console.log(chalk.cyan(`\nTool "${tool.name}":`));
        checks.forEach((check: string) => console.log(chalk.gray(`  ${check}`)));
      }
    });

    if (config.safety.requireUserApproval) {
      console.log(chalk.green('\n✅ Human-in-the-loop: All tools require user approval'));
    }
  }
}

// CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  const creator = new MCPServerCreator();
  creator.run().catch(console.error);
}

export { MCPServerCreator };
