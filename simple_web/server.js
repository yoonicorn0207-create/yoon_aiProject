// npm install express multer axios cors form-data

const express = require('express');
const multer = require('multer');
const axios = require('axios');
const cors = require('cors');
const FormData = require('form-data');
const path = require('path');

const app = express();
const port = 3000;

/**
 * 미들웨어 설정
 */
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // public 폴더를 정적 파일 루트로 설정

// 이미지 파일을 메모리에 임시 저장하기 위한 설정
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

/**
 * 프록시 API: 브라우저의 요청을 받아 FastAPI(8000) 서버로 전달합니다.
 */
app.post('/proxy/analyze', upload.single('image'), async (req, res) => {
    try {
        const { question } = req.body;
        const imageFile = req.file;

        if (!imageFile) {
            return res.status(400).json({ success: false, message: "이미지 파일이 누락되었습니다." });
        }

        // FastAPI의 multipart/form-data 규격에 맞춰 데이터 구성
        const formData = new FormData();
        formData.append('image', imageFile.buffer, {
            filename: imageFile.originalname,
            contentType: imageFile.mimetype,
        });
        formData.append('question', question || "이미지를 분석해주세요.");

        // FastAPI 서버(http://localhost:8000/analyze)로 요청 전송
        const response = await axios.post('http://localhost:8000/analyze', formData, {
            headers: {
                ...formData.getHeaders(),
            },
        });

        // 성공 결과 반환
        res.json(response.data);

    } catch (error) {
        console.error("AI 서버 통신 중 오류 발생:", error.message);
        res.status(500).json({
            success: false,
            message: "AI 분석 서버와의 통신에 실패했습니다. (FastAPI 구동 여부를 확인하세요)"
        });
    }
});

/**
 * 서버 시작
 */
app.listen(port, () => {
    console.log(`웹 인터페이스 서버가 가동되었습니다: http://localhost:${port}`);
});
