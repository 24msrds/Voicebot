// server.js
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Configuration, OpenAIApi } = require('openai');

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(express.static('public'));

if (!process.env.OPENAI_API_KEY) {
  console.warn('WARNING: OPENAI_API_KEY is not set. Set it in your environment before deploying.');
}
const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY
});
const openai = new OpenAIApi(configuration);

app.post('/api/chat', async (req, res) => {
  try {
    const { message, persona } = req.body;
    if (!message) return res.status(400).json({ error: 'message is required' });

    const systemPrompt = persona?.system || `You are a friendly, concise voice assistant that answers as the candidate would respond. Keep answers 1-3 sentences unless asked to expand. Use an encouraging tone and avoid jargon.`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: message }
    ];

    const completion = await openai.createChatCompletion({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      messages,
      max_tokens: 300,
      temperature: 0.6
    });

    const text = completion.data.choices[0].message.content.trim();
    res.json({ text });
  } catch (err) {
    console.error(err?.response?.data || err.message || err);
    res.status(500).json({ error: 'OpenAI error', details: err?.message || err });
  }
});

app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
