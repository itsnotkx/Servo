// Basic example of using the Servo SDK
const { Servo } = require('servo-sdk');

async function main() {
  // Step 1: Initialize the client
  const client = new Servo({
    apiKey: 'ADAWODWA',
    baseUrl: 'http://localhost:8000',
  });

  try {
    // Step 2: Send a request
    const result = await client.send('Who was the first president of the United States?');

    // Step 3: Receive and use the response
    console.log('Classification:', result.classification.complexity);
    console.log('Model:', result.target_model);
    console.log('Confidence:', result.classification.confidence);
    console.log('\nFull result:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
