<h1 align="center">📷 Instagram Clone (Django Project)</h1>

<p align="center">
  A full-stack web application clone of Instagram built <strong>entirely with Django</strong>.
  <br>
  This project uses Django's built-in templating engine for server-side rendering (SSR) of the user interface.
</p>

<p align="center">
  <img src="[LINK-TO-YOUR-SCREENSHOT.gif]" alt="Project Demo" width="80%">
  </p>

<hr>

## 🛠️ Tech Stack (تکنولوژی‌های استفاده شده)

<p align="center">
  <img src="https://img.shields.io/badge/-Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/-Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
</p>

<hr>

## ✨ Features (ویژگی‌ها)

* **User Authentication:** Secure user registration, login, and logout using Django's built-in auth system.
* **Create & View Posts:** Users can upload images with captions.
* **Home Feed:** View posts from all users in a timeline.
* **Like & Comment System:** Interactive liking and commenting on posts.
* **User Profiles:** View user-specific profiles and their posts.

<hr>

## 🚀 How to Run Locally (نحوه اجرا)

```bash
# 1. Clone the repository
git clone [https://github.com/abolfazl-io/Instagram-Project.git](https://github.com/abolfazl-io/Instagram-Project.git)

# 2. Navigate to the project directory
cd Instagram-Project

# 3. Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # (On Windows: venv\Scripts\activate)

# 4. Install requirements
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Run the server
python manage.py runserver

# 7. Open your browser
# (Go to [http://127.0.0.1:8000](http://127.0.0.1:8000))
