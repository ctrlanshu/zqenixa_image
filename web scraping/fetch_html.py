import requests

url = "https://apollodiagnostics.in/lifestyle-packages/obesity-94"
headers = {"User-Agent": "Mozilla/5.0"}
try:
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    with open("temp_page.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("Saved temp_page.html")
except Exception as e:
    print(f"Error: {e}")
