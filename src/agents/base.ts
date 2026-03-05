import Anthropic from '@anthropic-ai/sdk';

export interface AgentConfig {
  model: string;
  maxTokens: number;
  temperature: number;
  systemPrompt?: string;
}

export interface AgentResponse {
  content: string;
  model: string;
  tokensUsed: {
    input: number;
    output: number;
  };
  stopReason: string | null;
}

export class BaseAgent {
  protected client: Anthropic;
  protected config: AgentConfig;

  constructor(apiKey: string, config: AgentConfig) {
    this.client = new Anthropic({ apiKey });
    this.config = config;
  }

  async invoke(prompt: string): Promise<AgentResponse> {
    const response = await this.client.messages.create({
      model: this.config.model,
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature,
      system: this.config.systemPrompt,
      messages: [{ role: 'user', content: prompt }],
    });

    const textBlock = response.content.find((block) => block.type === 'text');

    return {
      content: textBlock?.type === 'text' ? textBlock.text : '',
      model: response.model,
      tokensUsed: {
        input: response.usage.input_tokens,
        output: response.usage.output_tokens,
      },
      stopReason: response.stop_reason,
    };
  }
}
