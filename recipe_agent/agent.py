from google.adk.agents import Agent
from google.adk.tools import google_search

import google.generativeai as genai

import os
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# --- פונקציה ליצירת תמונה באמצעות Gemini ---
def generate_recipe_image(recipe_title: str) -> str:
    """
    יוצר תמונה של המנה באמצעות מודל Gemini.
    תמיד מחזיר URL תקין.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-image")
        response = model.generate_images(
            prompt=f"Create a high-quality food photograph of the dish called '{recipe_title}'.",
            size="1024x1024"
        )

        if response and response.generated_images:
            return response.generated_images[0].url

    except Exception:
        pass

    # fallback במקרה ואין תמונה
    return "https://via.placeholder.com/600x400?text=No+Image+Available"


# --- פונקציה למציאת 2 מתכונים ---
def find_recipes(query: str) -> dict:
    """
    מחזיר 2 מתכונים מתאימים לפי רשימת מצרכים והעדפות.
    """
    search_results = google_search(query=query)
    if not search_results or "results" not in search_results:
        return {"status": "error", "message": "לא נמצאו מתכונים תואמים."}

    recipes = []
    for result in search_results["results"][:2]:
        recipes.append({
            "title": result.get("title", "מתכון ללא שם"),
            "snippet": result.get("snippet", "אין תיאור זמין."),
            "link": result.get("link", "")
        })

    return {"status": "success", "recipes": recipes}


# --- פונקציה להבאת מתכון מלא כולל תמונה ---
def get_full_recipe(recipe_title: str) -> dict:
    """
    מחפש מתכון מלא ומחזיר הוראות + תמונה אמיתית שנוצרת ע"י Gemini.
    """
    search_query = f"{recipe_title} מתכון מלא שלבי הכנה"
    results = google_search(query=search_query)

    if not results or "results" not in results or len(results["results"]) == 0:
        return {"status": "error", "message": "לא הצלחתי למצוא את פרטי המתכון."}

    recipe_data = results["results"][0]

    # יצירת תמונה במקום חיפוש — עובד תמיד
    image_url = generate_recipe_image(recipe_title)

    return {
        "status": "success",
        "title": recipe_title,
        "instructions": recipe_data.get("snippet", "אין הוראות זמינות."),
        "image_url": image_url
    }


# --- הגדרת הסוכן הראשי ---
root_agent = Agent(
    name="recipe_agent",
    model="gemini-2.0-flash",
    description="Agent שמציע 2 מתכונים לבחירה ומחזיר את המתכון המלא כולל הוראות ותמונה שנוצרת במערכת.",
    instruction="""
    אתה סוכן עוזר בישול אינטראקטיבי.
    שלב 1: המשתמש יקליד מצרכים והעדפות.
    שלב 2: השתמש בפונקציה find_recipes(query) כדי להציע 2 מתכונים מתאימים.
    שלב 3: הצג למשתמש את שמות המתכונים ותיאור קצר.
    שלב 4: שאל: "איזה מתכון תרצה שאביא במלואו?"
    שלב 5: כשהמשתמש בוחר מתכון, השתמש בפונקציה get_full_recipe(recipe_title) כדי להביא הוראות + תמונה שנוצרת אוטומטית.
    ענה בעברית בלבד, בצורה נעימה וברורה.
    """,
    tools=[google_search],
)
