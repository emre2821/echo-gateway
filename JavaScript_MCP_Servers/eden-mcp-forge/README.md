# MCP Server Creator

An interactive CLI tool that helps users create custom MCP (Model Context Protocol) servers with built-in safety features and human-in-the-loop permissions.

## Features

- 🛠️ **Interactive Tool Creation** - Step-by-step guided process to define MCP tools
- 🔒 **Safety-First Design** - Built-in validation and security checks
- 👥 **Human-in-the-Loop** - Configurable user approval requirements
- 📝 **Code Generation** - Automatic generation of production-ready MCP servers
- 🧪 **Template System** - Customizable Handlebars templates
- 📋 **Parameter Validation** - Zod schema generation for type safety
- 📚 **Documentation Generation** - Automatic README and test file creation

## Installation

```bash
npm install
npm run build
```

## Usage

### Interactive Mode (Recommended)

```bash
npm start
```

This will launch an interactive CLI that guides you through:

1. Server information (name, version, description)
2. Tool definition (parameters, annotations, handlers)
3. Safety configuration (approvals, restrictions, logging)
4. Output configuration (directory, package manager, tests/docs)

### Example Workflow

1. **Create a simple calculator tool:**

   - Tool name: `calculate-sum`
   - Parameters: `a` (number), `b` (number)
   - Handler: JavaScript implementation
   - Safety: Read-only annotation

2. **Add safety features:**

   - Require user approval: ✅
   - Enable logging: ✅
   - Restricted parameters: `password,token,secret`

3. **Generate server:**
   - Complete MCP server with TypeScript
   - Package.json with dependencies
   - README with documentation
   - Test files with examples

## Generated Server Structure

The tool creates a complete MCP server with:

```
mcp-server-output/
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── src/
│   └── index.ts         # Main server implementation
├── tests/
│   └── server.test.ts    # Generated tests
└── README.md             # Documentation
```

## Safety Features

### Human-in-the-Loop Permissions

All generated servers include configurable safety features:

- **User Approval**: Require explicit user consent before tool execution
- **Parameter Restrictions**: Block dangerous parameter names (password, token, etc.)
- **Execution Logging**: Detailed logs of all tool invocations
- **Time Limits**: Configurable maximum execution time
- **Operation Filtering**: Allow only specific operation types

### Code Validation

The tool includes automatic validation for:

- **Tool Names**: Must be kebab-case and valid format
- **Handler Code**: Syntax validation and security checks
- **Parameter Schemas**: Type-safe Zod schema generation
- **Annotations**: Safety hint validation

### Security Checks

Built-in protection against:

- `eval()` and `Function()` constructors
- File system access without explicit permission
- External network requests without approval
- Dangerous Node.js modules

## Configuration Options

### Server Configuration

- `name`: Server name (kebab-case)
- `version`: Semantic version (x.y.z)
- `description`: Human-readable description
- `author`: Optional author information
- `license`: License (default: MIT)

### Tool Configuration

- `name`: Tool name (kebab-case)
- `description`: Tool functionality description
- `parameters`: Zod schema definition
- `annotations`: Safety hints (readOnly, destructive, etc.)
- `handler`: JavaScript implementation

### Safety Configuration

- `requireUserApproval`: Enable human-in-the-loop
- `allowedOperations`: Whitelist of operation types
- `restrictedParameters`: Blacklist of parameter names
- `maxExecutionTime`: Timeout in seconds
- `enableLogging`: Execution logging toggle

## Development

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

### Development Mode

```bash
npm run dev
```

## Example Generated Server

Here's what a generated server looks like:

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const calculateSumSchema = z.object({
  a: z.number().describe("First number"),
  b: z.number().describe("Second number"),
});

class MyCalculatorServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "my-calculator",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "calculate-sum",
            description: "Calculates the sum of two numbers",
            inputSchema: zodToJsonSchema(calculateSumSchema),
            annotations: {
              title: "Sum Calculator",
              readOnlyHint: true,
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "calculate-sum") {
        const validatedArgs = calculateSumSchema.parse(args);
        return await this.handleCalculateSum(validatedArgs);
      }

      throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    });
  }

  private async handleCalculateSum(
    args: z.infer<typeof calculateSumSchema>
  ): Promise<any> {
    console.log(`[EXECUTE] calculate-sum`, args);

    const { a, b } = args;
    const result = a + b;

    return {
      content: [
        {
          type: "text",
          text: `The sum of ${a} and ${b} is ${result}`,
        },
      ],
    };
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("my-calculator MCP server running on stdio");
  }
}

const server = new MyCalculatorServer();
server.run().catch(console.error);
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all safety checks pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Resources

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/servers)
- [Safety Guidelines](https://modelcontextprotocol.io/docs/concepts/security)
