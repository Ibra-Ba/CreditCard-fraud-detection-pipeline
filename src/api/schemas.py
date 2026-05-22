from pydantic import BaseModel


class TransactionInput(BaseModel):
    trans_num:   str
    amt:         float
    category:    str
    gender:      str
    city_pop:    int
    lat:         float
    long:        float
    merch_lat:   float
    merch_long:  float
    dob:         str
    trans_date_trans_time: str


class PredictionOutput(BaseModel):
    trans_num:    str
    is_fraud:     bool
    fraud_score:  float