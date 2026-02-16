// TypeScript example with conversation management
import { Servo, Conversation, ComplexityLevel } from 'servo-sdk';

async function main() {
  // Initialize client
  const client = new Servo({
    apiKey: 'ADAWODWA',
    baseUrl: 'http://localhost:8000',
  });

  // Example 1: Simple request
  console.log('=== Simple Request ===');
  const result = await client.send('What is 2 + 2?');
  console.log('Complexity:', result.classification.complexity);
  console.log('Target Model:', result.target_model);

  // Example 2: With conversation context
  console.log('\n=== With Conversation ===');
  const conversation = new Conversation('You are a helpful assistant.');
  conversation.addUser('Hello!');
  conversation.addAssistant('Hi! How can I help you?');

  const result2 = await client.send('Tell me about TypeScript', {
    conversation,
  });
  console.log('Complexity:', result2.classification.complexity);

  // Example 3: Using individual methods
  console.log('\n=== Step-by-Step ===');
  const classification = await client.classify('Explain quantum computing');
  console.log('Classification:', classification);

  if (classification.complexity === ComplexityLevel.COMPLEX) {
    console.log('This is a complex query!');
  }

  const routing = await client.route(classification);
  console.log('Route:', routing);

  // Example 4: Health check
  console.log('\n=== Health Check ===');
  const health = await client.health();
  console.log('Health:', health);
}

main().catch(console.error);
