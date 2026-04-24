import mysql.connector
import os
from dotenv import load_dotenv

# .env 환경 변수 로드
load_dotenv(override=True)

def getDbConnection():
    """ MySQL 데이터베이스와의 연결을 생성하고 반환하는 함수입니다. """
    try:
        # 먼저 데이터베이스 지정 없이 접속하여 데이터베이스가 있는지 확인 및 생성
        temp_conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3307)),
            user=os.getenv("DB_USER", "kopouser"),
            password=os.getenv("DB_PASSWORD", "kopouser"),
            charset="utf8mb4"
        )
        cursor = temp_conn.cursor()
        db_name = os.getenv("DB_NAME", "ai_project_db")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        temp_conn.commit()
        cursor.close()
        temp_conn.close()

        # 실제 연결 시도
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3307)),
            user=os.getenv("DB_USER", "kopouser"),
            password=os.getenv("DB_PASSWORD", "kopouser"),
            database=db_name,
            charset="utf8mb4"
        )
        return connection
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None

def initializeDatabase():
    """ 테이블이 존재하지 않을 경우, 추출 결과를 저장할 테이블을 생성합니다. """
    try:
        dbConn = getDbConnection()
        if dbConn is not None:
            cursor = dbConn.cursor()
            # 사용 모델, 추출 텍스트, 생성 날짜(자동 생성)를 포함하는 테이블 생성
            createQuery = """
            CREATE TABLE IF NOT EXISTS extraction_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usedModel VARCHAR(100) NOT NULL,
                extractedText TEXT,
                createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(createQuery)
            dbConn.commit()
            cursor.close()
            dbConn.close()
            return {"success": True, "message": "Table initialized successfully"}
        else:
            return {"success": False, "message": "Connection failed during initialization"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def saveExtractionResult(usedModel, extractedText):
    """ 이미지에서 추출한 텍스트와 사용 모델 정보를 DB에 저장합니다. """
    try:
        dbConn = getDbConnection()
        if dbConn is not None:
            cursor = dbConn.cursor()
            # 데이터 삽입 쿼리 실행
            insertQuery = "INSERT INTO extraction_results (usedModel, extractedText) VALUES (%s, %s)"
            dataValues = (usedModel, extractedText)
            
            cursor.execute(insertQuery, dataValues)
            dbConn.commit()
            
            cursor.close()
            dbConn.close()
            return {"success": True, "message": "Extraction result saved successfully"}
        else:
            return {"success": False, "message": "Database connection failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # 스크립트 단독 실행 시 테이블 생성 확인
    result = initializeDatabase()
    print(result)
