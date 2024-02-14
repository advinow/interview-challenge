import csv
from io import StringIO
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import psycopg2

from models import Business, Symptom, business_symptom_m2m
from sessions import session_scope, get_db, Session
from sqlalchemy import insert, orm
from sqlalchemy.exc import IntegrityError


router = APIRouter()


@router.get('/status')
async def get_status():
    try:
        return {"Health OK"}

    except Exception as e:
        return {'Error: ' + str(e)}


class CsvImportBusiness(BaseModel):
    id: int = Field(alias='Business ID')
    name: str = Field(alias='Business Name')

class CsvImportSymptom(BaseModel):
    code: str = Field(alias='Symptom Code')
    name: str = Field(alias='Symptom Name')
    diagnostic: bool = Field(alias='Symptom Diagnostic')


def validate_csv(file: UploadFile):
    contents = file.file.read()
    buffer = StringIO(contents.decode('utf-8'))
    reader = csv.DictReader(buffer)

    validated_data =  (
        (CsvImportBusiness(**row), CsvImportSymptom(**row))
        for row in reader
    )

    return validated_data


def dedupe_data(validated_data):
    b_set, s_set = set(), set()
    businesses, symptoms = [], []

    for tup in validated_data:
        if tup[0].id not in b_set:
            b_set.add(tup[0].id)
            businesses.append(tup[0])
        
        if tup[1].code not in s_set:
            s_set.add(tup[1].code)
            symptoms.append(tup[1])

    return businesses, symptoms

def import_csv_businesses(businesses):

    with session_scope() as db:
        
        pks = {id for id in db.query(Business.id).distinct()}

        for b in filter(lambda b: b.id not in pks, businesses):
            try:
                db.execute(insert(Business).values(**b.dict()))
                db.flush()
            except IntegrityError:
                db.rollback()
                continue

def import_csv_symptoms(symptoms):

    with session_scope() as db:

        pks = {code for code in db.query(Symptom.code)}

        for s in filter(lambda s: s.code not in pks, symptoms):
            try:
                db.execute(insert(Symptom).values(**s.dict()))
                db.flush()
            except IntegrityError:
                db.rollback()
                continue


@router.post('/csv')
async def import_csv(file: UploadFile = File(...)):
    try:
        validated_data = validate_csv(file)
        m2ms = [(tup[0].id, tup[1].code) for tup in validated_data]
    
    except Exception as e:
        file.file.close()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"result": f"ERROR: {e}"}
        )
        
    businesses, symptoms = dedupe_data(validated_data)
    
    import_csv_businesses(businesses)
    import_csv_symptoms(symptoms)

    with session_scope() as db:

        for tup in m2ms:
            try:
                db.execute(
                    insert(business_symptom_m2m).values(
                        business_id=tup[0],
                        symptom_code=tup[1]
                    )
                )
                db.flush()
            except IntegrityError:
                db.rollback()
                continue
    

    file.file.close()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"result": "SUCCESS"}
    )


class SymptomResource(BaseModel):
    code: str
    name: str
    diagnostic: bool

    class Config:
        orm_mode = True

class BusinessResource(BaseModel):
    id: int
    name: str
    symptoms: List[SymptomResource]
    
    class Config:
        orm_mode = True


@router.get("/resources", response_model=list[BusinessResource])
def get_resources(
    bid: int | None = None, 
    diagnostic: bool | None = None, 
    db: Session = Depends(get_db)
) -> list[BusinessResource]:

    if diagnostic is not None:
        query = (
            db.query(Business) \
            .join(Symptom, Business.symptoms)
            .options(orm.contains_eager(Business.symptoms))
            .filter(Symptom.diagnostic == diagnostic)
        )
    
    else:
        query = (
            db.query(Business) \
            .join(Symptom, Business.symptoms)
        )

    if bid:
        query = query.filter(Business.id == bid)
    
    res = query.all()

    return res

