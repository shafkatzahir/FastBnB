from pydantic import BaseModel, Field
import datetime

class BookingBase(BaseModel):
    property_id: int
    start_date: datetime.date
    end_date: datetime.date

class BookingCreate(BookingBase):
    # user_id will come from the JWT token
    pass

class BookingRead(BookingBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
