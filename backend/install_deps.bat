@echo off
echo Installing FaceAttend-KE dependencies...
echo.

cd /d C:\Users\USER\faceattend-ke\backend
call venv\Scripts\activate

echo Step 1/5: Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo Step 2/5: Installing numpy and Pillow...
pip install opencv-python-headless numpy==1.24.3 Pillow

echo Step 3/5: Installing dlib...
pip install dlib --only-binary dlib

echo Step 4/5: Installing face_recognition (includes models)...
pip install face-recognition==1.3.0

echo Step 5/5: Installing Flask and other dependencies...
pip install flask-cors flask-login flask-sqlalchemy flask-migrate flask-limiter python-dotenv pymysql mysql-connector-python bcrypt pytz

echo.
echo Installation complete! Testing...
python -c "import face_recognition; print('✅ face_recognition: OK')"
python -c "import flask; print('✅ flask: OK')"
python -c "import pymysql; print('✅ pymysql: OK')"

echo.
echo You can now run: python run.py
pause