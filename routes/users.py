from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from config_db import collection  # Import the MongoDB collection
import cloudinary.uploader
import config_cloudinary  # Ensure this is imported to configure Cloudinary
import logging
from bson import ObjectId
import bcrypt
from utils import create_access_token
from datetime import timedelta

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@router.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    birthday: str = Form(...),
    disabled: bool = Form(False),
    file: UploadFile = File(...)
):
    try:
        # Check if the user already exists
        if collection.find_one({"email": email}):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Upload the image to Cloudinary
        try:
            result = cloudinary.uploader.upload(file.file)
            img_url = result.get("secure_url")
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
        
        # Convert birthday to date
        try:
            birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Invalid date format: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        
        # Save the user to the MongoDB database
        user_dict = {
            "username": username,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "birthday": birthday_date,
            "img_path": img_url,
            "disabled": disabled
        }
        inserted_user = collection.insert_one(user_dict)
        user_dict["_id"] = str(inserted_user.inserted_id)
        
        return JSONResponse(content={"message": "User registered successfully", "user": user_dict})
    
    except HTTPException as e:
        logger.error(f"HTTPException: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    
@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        # Find the user by email
        user = collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        # Verify the password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        # Create JWT token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        
        # Log the successful response with token
        logger.info(f"User {email} logged in successfully. Token: {access_token}")
        
        return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    
    except HTTPException as e:
        logger.error(f"HTTPException: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")