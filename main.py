from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates 

from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from typing import Annotated, Optional


from utils.mocking import *
from policies.enforce import *

templates = Jinja2Templates(directory="/app/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    mock_patient_case()
    yield

app = FastAPI(lifespan=lifespan)



#wellness form 
@app.get("/", response_class=HTMLResponse)
async def root(request : Request):

    return templates.TemplateResponse(
        request=request, name="form.html"
    )



@app.post("/submit_form")
async def intake_form(
    patient_id: Annotated[str, Form()],
    pain_level: Annotated[int, Form()],
    pain_trend: Annotated[str, Form()],
    energy_level: Annotated[int, Form()],
    energy_trend: Annotated[str, Form()],
    drinking: Annotated[str, Form()],
    smoking: Annotated[str, Form()],
    wound_color: Annotated[str, Form()],
    free_response: Annotated[Optional[str], Form()] = None,
):
    
    param_dict = {
        "patient_id": patient_id,
        "pain_level": pain_level,
        "pain_trend": pain_trend,
        "energy_level": energy_level,
        "energy_trend": energy_trend,
        "drinking": drinking,
        "smoking": smoking,
        "wound_color": wound_color,
        "free_response": free_response.strip() if free_response else None,
    }

    return await process_form(param_dict)



from pymongo import AsyncMongoClient
import pprint


#background form processing begins
async def process_form(param_dict : dict[str, str]):

    async with AsyncMongoClient("mongodb://db:27017/") as client:

        db = client["caregiver_app"]

        patient_cases = db["patient_cases"]
        patient_records = db["patient_records"]

        #check user existence  
        patient_existence = await patient_cases.find_one({"patient_id" : param_dict["patient_id"]})

        #Non-existant user
        if patient_existence is None:
            raise HTTPException(status_code=409, detail="non-existant patient_id")

        #record dating for time series checks 
        date = datetime.now().strftime("%d-%m-%Y")
        param_dict['date'] = date 


        pprint.pprint(param_dict)
        #insert newest record 
        await patient_records.insert_one(param_dict)

        flags = await enforce_policies(patient_existence['operation'], param_dict['patient_id'], patient_records)  

        if not flags: 
            return ("no explicit flags have been found in patient records")
        
        return flags 