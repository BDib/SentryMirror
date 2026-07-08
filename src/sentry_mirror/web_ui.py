from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sentry_mirror.database import DatabaseManager

app = FastAPI()
db = DatabaseManager("simulated_database.db")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # Fetch a sample table from your inferred database
    data = await db.get_from_db("users") 
    
    # Simple HTML representation
    rows = "".join([f"<tr><td>{row['id']}</td><td>{row['name']}</td></tr>" for row in data])
    
    return f"""
    <html>
        <body>
            <h1>SentryMirror Dashboard</h1>
            <table border="1">
                <tr><th>ID</th><th>Name</th></tr>
                {rows}
            </table>
        </body>
    </html>
    """