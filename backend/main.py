import random
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, constr
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI(
    title="Rynex API Engine (Google Sheets)",
    description="Google Sheets backed Core API for Rynex",
    version="1.1.0"
)

# 1. Google Sheets API Configuration
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    # credentials.json file se authenticate kar rahe hain
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
    client = gspread.authorize(creds)
    
    # Apni Google Sheet ka naam yahan sahi se daalna
    # Aur "Users" tab/worksheet ko open karna
    sheet = client.open("Rynex_Database").worksheet("Users")
except Exception as e:
    print(f"🛑 Google Sheets Connection Error: {e}")
    sheet = None

# 2. Pydantic Data Validation Schema
class SendOTPRequest(BaseModel):
    phone_number: constr(min_length=10, max_length=10)

# Mock SMS Gateway for testing
def send_sms_gateway(phone: str, otp: str):
    print(f"🚀 [MOCK SMS] Sending OTP {otp} to +91-{phone}")
    return True

# 3. Core Root Endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Rynex Google Sheets API Engine 🚀"}

# 4. Send OTP API Endpoint
@app.post("/api/auth/send-otp")
def send_otp(request: SendOTPRequest):
    if sheet is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Google Sheet connection is not initialized."
        )
    
    try:
        # Sheet ka saara data fetch karein check karne ke liye
        all_records = sheet.get_all_records()
        
        user_exists = False
        # Check karein ki kya yeh mobile number pehle se sheet mein hai
        for record in all_records:
            if str(record.get("Phone_Number")) == request.phone_number:
                user_exists = True
                break

        generated_otp = str(random.randint(100000, 999999))

        if not user_exists:
            # Agar naya student hai, toh details generate karein
            user_id = str(uuid.uuid4())
            created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Order strictly wahi hona chahiye jo Google Sheet ke columns ka hai:
            # User_ID | Phone_Number | Full_Name | College_Name | Status | Created_At
            sheet.append_row([user_id, request.phone_number, "", "", "Active", created_at])
            user_msg = "New student registered in Google Sheet successfully."
        else:
            user_msg = "Existing student login detected."

        # OTP trigger karein
        send_sms_gateway(request.phone_number, generated_otp)

        return {
            "status": "success",
            "message": f"OTP processed. {user_msg}",
            "expires_in": "5 minutes"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Google Sheet Operations Error: {str(e)}"
        )
