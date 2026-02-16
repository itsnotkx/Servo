import { Servo, ProcessingResult } from 'servo-sdk';

async function main() {
  const client = new Servo({
    apiKey: 'ADAWODWA',
    baseUrl: 'http://localhost:8000',
    defaultUserId: 'default_user'
  });

  try {
    const result: ProcessingResult = await client.send('What is 2 + 2?', undefined, { useQuickClassify: true });
    console.log('Category ID:', result.classification.category_id);
    console.log('Category Name:', result.classification.category_name);
    console.log('Model:', result.target_model);
    console.log('LLM Response:', result.llm_response);
    console.log('\nFull result:', JSON.stringify(result, null, 2));
  } catch (error) {
    console.error('Error:', error);
  }
}

main();