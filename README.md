# Developer Documentation for Running the To-Do App

This documentation will guide you through setting up and running the To-Do App in your local environment.

---

## **Prerequisites**

1. **Python**: Ensure Python 3.8 or higher is installed.
2. **MySQL**: Install MySQL and set up a database.
3. **Environment Variables**: Create a `.env` file to securely store sensitive information.
4. **Flask and Required Libraries**: Install Flask and the necessary dependencies.

---

## **Setup Instructions**

### **1. Clone the Repository**
- Clone or download the project to your local machine:
  ```bash
  git clone <repository-url>
  cd <repository-directory>
  ```

---

### **2. Install Dependencies**
- Use `pip` to install the required Python packages:
  ```bash
  pip install -r requirements.txt
  ```

---

### **3. Set Up the MySQL Database**

1. **Create a MySQL Database**:
   ```sql
   CREATE DATABASE todo_app;
   USE todo_app;
   ```

2. **Create the `Users` Table**:
   ```sql
   CREATE TABLE Users (
       id INT AUTO_INCREMENT PRIMARY KEY,
       email VARCHAR(255) NOT NULL UNIQUE,
       password_hash VARCHAR(255),
       google_id VARCHAR(255),
       is_guest BOOLEAN DEFAULT FALSE
   );
   ```

3. **Create the `Tasks` Table**:
   ```sql
   CREATE TABLE Tasks (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id INT NOT NULL,
       task_name VARCHAR(255) NOT NULL,
       due_date DATE,
       priority ENUM('Low', 'Medium', 'High'),
       completed BOOLEAN DEFAULT FALSE,
       completed_on DATE,
       FOREIGN KEY (user_id) REFERENCES Users(id)
   );
   ```

---

### **4. Configure Environment Variables**
Create a `.env` file in the root directory with the following variables:
```
# MySQL Database Config
DB_HOST=localhost
DB_USER=<your-database-username>
DB_PASSWORD=<your-database-password>

# Google OAuth Config
CLIENT_ID=<your-google-client-id>
CLIENT_SECRET=<your-google-client-secret>
```

Replace `<your-database-username>`, `<your-database-password>`, `<your-google-client-id>`, and `<your-google-client-secret>` with your actual configuration values.

---

### **5. Run the Application**
- Start the Flask development server:
  ```bash
  python app.py
  ```
- By default, the app will run on `http://127.0.0.1:5000`.

---

### **6. Access the Application**
- Open your web browser and go to `http://127.0.0.1:5000` to access the app.

---

## **Environment Details**
- **Python Packages**:
  - Flask
  - Flask-Mail
  - bcrypt
  - mysql-connector-python
  - Authlib
  - python-dotenv

- **Database**:
  - MySQL
  - Tables: `Users`, `Tasks`

---

## **Optional: Running in Production**
1. Use a production-ready web server like **Gunicorn** or **uWSGI**.
2. Configure a **reverse proxy** with **Nginx** or **Apache**.
3. Use a secure MySQL server and production OAuth credentials.

---

## **Common Issues and Fixes**

1. **`mysql.connector.errors.ProgrammingError`**:
   - Ensure your database and tables are correctly created.
   - Verify the `.env` file has correct credentials.

2. **OAuth Errors**:
   - Verify Google OAuth credentials.
   - Ensure `redirect_uri` in Google Console matches `http://127.0.0.1:5000/google/callback`.

3. **Dependency Errors**:
   - Run `pip install -r requirements.txt` again to resolve missing packages.

---

## **Support**
For further assistance, contact the development team at `developer@todoapp.com`.

Enjoy building and running the To-Do App! 🎉
