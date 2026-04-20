const express = require('express');
const cors = require('cors');
const app = express();

// Cho phép CORS để website khách hàng có thể gọi API
app.use(cors());
app.use(express.json());

// Phục vụ các file tĩnh (giả lập CDN) từ thư mục public
app.use(express.static('public'));

const validKeys = {
    'ABC123XYZ': { name: 'Customer A', requests: 0 }
};

// API Endpoint nhận câu hỏi
app.post('/api/chat', async (req, res) => {
    const apiKey = req.headers['x-api-key'];
    
    if (!validKeys[apiKey]) {
        return res.status(401).json({ error: 'Invalid API key' });
    }
    
    const { question } = req.body;
    validKeys[apiKey].requests++;
    
    // Nơi bạn sẽ gọi Model AI hoặc bridge qua hệ thống Multi-Agent của bạn
    const answer = `[Bot]: Bạn vừa hỏi "${question}". Đây là phản hồi từ localhost:8000!`;
    
    // Giả lập delay của AI
    setTimeout(() => {
        res.json({ answer: answer });
    }, 500);
});

app.listen(8000, () => {
    console.log('🚀 Server & CDN đang chạy tại http://localhost:8000');
});