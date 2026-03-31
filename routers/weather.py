from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from services import weather_service
import schemas

router = APIRouter(prefix="/weather", tags=["weather"])


class WeatherRequest(BaseModel):
    city: str


@router.get("", response_model=List[schemas.WeatherResponse])
def get_weather(city: str = "北京", days: int = 3):
    try:
        if days == 1:
            weather = weather_service.get_current_weather(city)
            return [weather]
        else:
            forecasts = weather_service.get_forecast_weather(city, days)
            return forecasts
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"天气服务错误: {str(e)}")
