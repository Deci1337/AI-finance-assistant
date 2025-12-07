from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from gigachat_integration import get_access_token, chat_completion, MODEL

app = FastAPI(title="AI Finance Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExpenseAnalysisRequest(BaseModel):
    text: str

class ExpenseAnalysisResponse(BaseModel):
    expenses: list
    summary: dict
    insights: str

def analyze_expenses(text: str) -> dict:
    token = get_access_token()
    if not token:
        raise HTTPException(status_code=500, detail="Failed to get access token")
    
    prompt = f"""Ты финансовый ассистент. Проанализируй следующий текст о тратах пользователя и извлеки структурированную информацию.

Текст пользователя: {text}

ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста со следующей структурой:
{{
    "expenses": [
        {{
            "amount": число,
            "category": "категория",
            "description": "описание",
            "date": "дата если указана"
        }}
    ],
    "summary": {{
        "total": общая сумма,
        "by_category": {{"категория": сумма}},
        "count": количество трат
    }},
    "insights": "краткий анализ и рекомендации"
}}

Если дата не указана, используй сегодняшнюю дату. Категории могут быть: Продукты, Транспорт, Развлечения, Одежда, Здоровье, Образование, Другое."""

    result = chat_completion(token, prompt)
    
    if 'error' in result:
        raise HTTPException(status_code=500, detail=f"GigaChat error: {result}")
    
    try:
        response_text = result['choices'][0]['message']['content']
        import json
        import re
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            analysis = json.loads(json_str)
            
            if 'expenses' not in analysis:
                analysis['expenses'] = []
            if 'summary' not in analysis:
                analysis['summary'] = {}
            if 'insights' not in analysis:
                analysis['insights'] = "Анализ выполнен успешно"
                
            return analysis
        else:
            return {
                "expenses": [],
                "summary": {"total": 0, "by_category": {}, "count": 0},
                "insights": response_text[:500]
            }
    except json.JSONDecodeError as e:
        return {
            "expenses": [],
            "summary": {"total": 0, "by_category": {}, "count": 0},
            "insights": f"Ошибка парсинга JSON: {str(e)}. Ответ модели: {response_text[:200]}"
        }
    except Exception as e:
        return {
            "expenses": [],
            "summary": {"total": 0, "by_category": {}, "count": 0},
            "insights": f"Ошибка обработки: {str(e)}"
        }

@app.post("/api/analyze-expenses", response_model=ExpenseAnalysisResponse)
async def analyze_expenses_endpoint(request: ExpenseAnalysisRequest):
    analysis = analyze_expenses(request.text)
    return ExpenseAnalysisResponse(**analysis)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
