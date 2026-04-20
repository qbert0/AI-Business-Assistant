const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8000;
const BASE_URL = process.env.PLUGIN_BASE_URL || `http://localhost:${PORT}`;
const PUBLIC_DIR = path.join(__dirname, 'public');

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(PUBLIC_DIR));

const validApiKeys = {
    'ABC123XYZ': { name: 'Customer A', requests: 0, allowedOrigins: ['http://localhost:3000'] },
};

const pluginConfigs = {};

function generateApiKey() {
    return `plugin_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function createEnvelope(data, message = 'OK', customCode = 200) {
    return {
        status: customCode,
        success: customCode === 2001,
        message,
        data,
    };
}

function getHeaderApiKey(req) {
    return req.headers['x-api-key'] || req.query.apiKey || req.body.apiKey;
}

function validateApiKey(apiKey) {
    return typeof apiKey === 'string' && validApiKeys[apiKey];
}

function sendOk(res, data) {
    return res.status(200).json(data);
}

function sendWrapped(res, data, message = 'OK', customCode = 2001) {
    return res.status(200).json(createEnvelope(data, message, customCode));
}

app.get('/health', (req, res) => {
    return sendOk(res, { status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/plugin/info', (req, res) => {
    return sendOk(res, {
        name: 'AI Chat Plugin Service',
        version: '1.0.0',
        baseUrl: BASE_URL,
        docs: `${BASE_URL}/plugin`,
        description: 'Service cung cap giao dien chat embeddable va API chat cho cac website doi tac.',
    });
});

app.post('/plugin/register', (req, res) => {
    const { origin, siteName, apiKey, theme } = req.body;
    if (!origin) {
        return res.status(400).json({ error: 'Missing origin parameter.' });
    }

    const assignedKey = apiKey || generateApiKey();
    validApiKeys[assignedKey] = {
        name: siteName || origin,
        requests: 0,
        allowedOrigins: [origin],
    };

    pluginConfigs[origin] = {
        siteName: siteName || 'Partner Website',
        apiKey: assignedKey,
        theme: theme || { primary: '#0084ff', accent: '#ffffff' },
        registeredAt: new Date().toISOString(),
    };

    const embedSnippet = `<script src=\"${BASE_URL}/plugin/widget.js\"></script>\n<script>AIChat.init({ apiKey: '${assignedKey}', baseUrl: '${BASE_URL}', widgetTitle: '${pluginConfigs[origin].siteName}' });</script>`;

    return sendWrapped(res, {
        origin,
        config: pluginConfigs[origin],
        widgetUrl: `${BASE_URL}/plugin/widget.js`,
        embedSnippet,
    }, 'Plugin registered successfully', 2001);
});

app.get('/plugin/config', (req, res) => {
    const origin = req.query.origin;
    if (!origin || typeof origin !== 'string') {
        return res.status(400).json({ error: 'Missing origin query parameter.' });
    }
    const config = pluginConfigs[origin];
    if (!config) {
        return res.status(404).json({ error: 'Plugin configuration not found for this origin.' });
    }

    return sendWrapped(res, {
        origin,
        config,
        widgetUrl: `${BASE_URL}/plugin/widget.js`,
    }, 'Plugin configuration retrieved', 2001);
});

app.post('/api/validate-key', (req, res) => {
    const apiKey = getHeaderApiKey(req);
    if (!validateApiKey(apiKey)) {
        return res.status(401).json({ error: 'Invalid API key.' });
    }
    return sendWrapped(res, { valid: true, apiKey }, 'API key is valid', 2001);
});

app.post('/api/chat', async (req, res) => {
    const apiKey = getHeaderApiKey(req);
    if (!validateApiKey(apiKey)) {
        return res.status(401).json({ error: 'Invalid API key.' });
    }

    const { question } = req.body;
    if (!question || typeof question !== 'string') {
        return res.status(400).json({ error: 'Missing question in request body.' });
    }

    validApiKeys[apiKey].requests += 1;

    const answer = `[Bot]: B?n v?a h?i "${question}". Ðây là ph?n h?i t? Plugin-service t?i ${BASE_URL}.`;
    const responseData = {
        question,
        answer,
        apiKey,
        requests: validApiKeys[apiKey].requests,
    };

    return sendOk(res, responseData);
});

app.listen(PORT, () => {
    console.log(`?? Plugin Service running at ${BASE_URL}`);
});
