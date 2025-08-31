from flask import request, jsonify, render_template, redirect, url_for
from. import home_bp

# --- Login Routes ---

@home_bp.route('/', methods=['POST','GET'])
def login_post():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .nav-list {
            list-style-type: none;
            padding: 0;
            margin: 0;
        }
        .nav-list li {
            margin-bottom: 15px;
        }
        .nav-list a {
            display: block;
            background-color: #007bff;
            color: white;
            padding: 15px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background-color 0.3s ease;
        }
        .nav-list a:hover {
            background-color: #0056b3;
        }
        /* Differentiating the 'info' link */
        .nav-list a.info-link {
            background-color: #6c757d;
        }
        .nav-list a.info-link:hover {
            background-color: #5a6268;
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>Project Navigation</h1>
        <ul class="nav-list">
            <li><a href="/auth/admin/login">For Admin Dashboard</a></li>
            <li><a href="/auth/employee/login">For Employee Dashboard</a></li>
            <li><a href="/dashboard">For Monitoring App</a></li>
            <li><a href="#" class="info-link">For Info About This Project</a></li>
        </ul>
    </div>

</body>
</html>'''


