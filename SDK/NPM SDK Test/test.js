const { Servo } = require('servo-sdk');

async function main() {
  const client = new Servo({
    apiKey: 'ADAWODWA',
    baseUrl: 'http://localhost:8000',
    defaultUserId: 'default_user'
  });

  try {
    console.log('Testing Servo SDK...');
    
    // Test health endpoint first
    const health = await client.health();
    console.log('Health check:', health);
    
    // Test categories
    const categories = await client.categories();
    console.log('\nAvailable categories:', categories.categories.map(c => c.id));
    
    // Test send
    const result = await client.send('What is 2 + 2?');
    console.log('\nResult:');
    console.log('- Category ID:', result.classification.category_id);
    console.log('- Category Name:', result.classification.category_name);
    console.log('- Model:', result.target_model);
    console.log('- Confidence:', result.classification.confidence);
    console.log('- LLM Response:', result.llm_response);
    
  } catch (error) {
    console.error('Error:', error.message);
    if (error.cause) {
      console.error('Cause:', error.cause.message);
    }
  }
}

main();
