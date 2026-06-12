import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import app

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

client = app.test_client(use_cookies=True)

print("Attempting to log in as 'diagnostic_user'...")
try:
    login_res = client.post('/login', data={
        'email': 'diagnostic_user',
        'password': 'password123',
        'remember': False
    })

    print("Login Response Status Code:", login_res.status_code)
    print("Redirect Location:", login_res.headers.get('Location'))
    
    # GET dashboard page (following redirect)
    print("GETting /dashboard...")
    dash_res = client.get('/dashboard')
    print("Dashboard Response Status Code:", dash_res.status_code)
    
    if dash_res.status_code == 500:
        print("Error: Received 500 on /dashboard!")
        print("Response HTML (first 1500 chars):")
        print(dash_res.data.decode('utf-8')[:1500])
        # Write to file
        with open("scratch/error_dashboard_500.html", "w", encoding="utf-8") as f:
            f.write(dash_res.data.decode('utf-8'))
        print("Saved detailed error page to scratch/error_dashboard_500.html")
    else:
        print("Dashboard loaded successfully! Page content length:", len(dash_res.data))
except Exception as e:
    import traceback
    print("Exception occurred:")
    traceback.print_exc()
