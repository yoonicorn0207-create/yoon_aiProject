# pip install fastapi uvicorn ollama openai python-multipart python-dotenv

import os
import base64
import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import ollama
from openai import OpenAI

from database import saveExtractionResult, initializeDatabase

"""
핵심 설정 로드 및 FastAPI 앱 초기화
"""
load_dotenv(override=True)
app = FastAPI()

@app.on_event("startup")
async def startupEvent():
    """ 서버 시작 시 데이터베이스 테이블을 초기화합니다. """
    initResult = initializeDatabase()
    if initResult["success"] == True:
        print("데이터베이스 초기화 성공: 테이블이 준비되었습니다.")
    else:
        print(f"데이터베이스 초기화 실패: {initResult['message']}")


# CORS 설정: 모든 접속 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def encodeImage(imageFile):
    """ 이미지를 base64 문자열로 인코딩하는 함수입니다. """
    try:
        return base64.b64encode(imageFile).decode('utf-8')
    except Exception as e:
        raise e


@app.post("/analyze")
async def analyzeImage(image: UploadFile = File(...), question: str = Form("이 이미지에 대해 설명해주세요.")):
    """ 사용자가 업로드한 이미지를 분석하여 텍스트 추출 및 답변을 제공하는 API입니다. """
    try:
        useModel = os.getenv("USE_MODEL", "OLLAMA")
        imageData = await image.read()
        modelName = ""
        
        if useModel == "OLLAMA":
            # Ollama 로직 실행
            modelName = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
            response = ollama.chat(
                model=modelName,
                messages=[{
                    'role': 'user',
                    'content': question,
                    'images': [imageData]
                }]
            )
            finalResult = response['message']['content']
            
        elif useModel == "GPT":
            # OpenAI 로직 실행
            modelName = "gpt-4o"
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            base64Image = encodeImage(imageData)
            
            response = client.chat.completions.create(
                model=modelName,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64Image}",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )
            finalResult = response.choices[0].message.content
            
        else:
            return {"success": False, "message": "설정된 모델이 유효하지 않습니다."}

        # 명시적 반복문 예시 (결과 텍스트를 한 글자씩 검증하거나 처리할 때 사용 가능)
        processedText = ""
        for i in range(0, len(finalResult)):
            processedText += finalResult[i]
        
        # 분석 결과를 데이터베이스에 저장
        dbSaveResult = saveExtractionResult(modelName, processedText)
        
        if dbSaveResult["success"] == True:
            return {"success": True, "result": processedText, "dbStatus": "Saved"}
        else:
            # DB 저장에 실패하더라도 분석 결과는 반환하되, 상태를 알림
            return {"success": True, "result": processedText, "dbStatus": f"Save Failed: {dbSaveResult['message']}"}

    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # 주피터 노트북 환경에서 실행하기 위한 설정
    import nest_asyncio
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)
