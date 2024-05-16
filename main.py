from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import stripe
from typing import Dict


app = FastAPI()

stripe.api_key = "sk_test_51PGPJaSEcKlzWgP0w7EhtXqVPr0J1f6T3GgihxqEIizUowzuw0l9F3mOZ69erognb2Eli3YLomOtehrNhsSvTNUP00kkmQnuuy"


@app.get('/')
async def check():
    return 'hello'


origins = [
    "http://localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class PatientBase(BaseModel):
    name: str
    age: str
    contact_num: str
    date_of_birth: str


class PatientModel(PatientBase):
    id: int


class PaymentRequest(BaseModel):
    amount: int
    user_id: int
    doctor_name: str


class PaymentModel(PaymentRequest):
    id: int
    payment_link: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

models.Base.metadata.create_all(bind=engine)

# Api to post patients
@app.post("/patients/", response_model=PatientModel)
async def create_patient(patient: PatientBase, db: db_dependency):
    print('he')
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Api to get patients
@app.get("/patients/", response_model=List[PatientModel])
async def read_patients(db: db_dependency, skip: int=0, limit: int=100):
    patients = db.query(models.Patient).offset(skip).limit(limit).all()
    return patients


# This function creates a product and price in Stripe dashboard
def create_product_and_price(amount, patient_name):
    try:
        product = stripe.Product.create(
            name= patient_name,
            description="Description"
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency="usd"
        )

        return product.id, price.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# this function save the payment link created over stripe
def save_payment_link(db: Session, user_id: int, payment_link: str, amount: int, doctor_name: str):
    db_payment_link = models.PaymentLink(user_id=user_id, payment_link=payment_link, amount=amount, doctor_name=doctor_name)
    db.add(db_payment_link)
    db.commit()
    db.refresh(db_payment_link)
    return db_payment_link

# function to return payment links
def get_payment_links(db: Session):
    return db.query(models.PaymentLink).all()


# function to return userwise payment links
def get_user_payment_links(db: Session, user_id: int):
    return db.query(models.PaymentLink).filter(models.PaymentLink.user_id == user_id).all()


@app.post("/create_payment_link/", response_model=PaymentModel)
async def create_payment_link(db: db_dependency, payment_request: PaymentRequest):
    try:
        product_id, price_id = create_product_and_price(payment_request.amount, 'Raj')

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        payment_link = session.url
        saved_payment_link = save_payment_link(db=db, user_id=payment_request.user_id, 
                                               payment_link=payment_link, 
                                               amount=payment_request.amount,
                                               doctor_name=payment_request.doctor_name)  

        return saved_payment_link
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payment_links/", response_model=List[PaymentModel])
async def get_all_payment_links(db: db_dependency):
    payment_links = get_payment_links(db)
    return payment_links


# api to get userwise payment link
@app.get("/user_payment_links/{user_id}", response_model=List[PaymentModel])
async def get_user_payment_links_endpoint(user_id: int, db: db_dependency):
    payment_links = get_user_payment_links(db, user_id)
    return payment_links