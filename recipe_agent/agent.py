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

    # fallback במקרה שאין תמונה
    return "https://via.placeholder.com/600x400?text=No+Image+Available"


# --- פונקציה למציאת 2 מתכונים ---
def find_recipes(ingredients: str, preference: str) -> dict:
    """
    מחפש 2 מתכונים לפי מצרכים + העדפה.
    """
    query = f"מתכונים עם {ingredients} שמתאימים ל {preference}"
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
    מחפש מתכון מלא ומחזיר הוראות + תמונה שנוצרת ע"י Gemini.
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
    description="Agent שמציע 2 מתכונים לבחירה ומחזיר מתכון מלא כולל הוראות ותמונה.",
    instruction="""
    אתה סוכן בישול חכם ומקצועי.
    תפקידך לסייע למשתמש למצוא מתכונים לפי מצרכים, להתאים אותם להעדפות,
    ולהציג מתכון מלא כולל תמונת מנה.

    אופן העבודה שלך:

    1. המשתמש ימסור רשימת מצרכים שיש לו בבית.

    2. שאל את המשתמש:
       "האם יש לך העדפות למתכון? לדוגמה: קר / חם / מהיר / קל / פרווה / חלבי / חריף / בריא / לא משנה."

    3. לאחר שהמשתמש עונה — הפעל:
       find_recipes(ingredients, preference)
       והצג שני מתכונים מתאימים: שם + תיאור קצר.

    4. שאל את המשתמש:
       "איזה מתכון תרצה שאביא עבורך במלואו?"

    5. כשהמשתמש בוחר — הפעל:
       get_full_recipe(recipe_title)

    6. החזר למשתמש:
       • שם המנה
       • הוראות הכנה
       • תמונה שנוצרה באמצעות Gemini (במידה ומותר על-ידי נטפרי)

    הנחיות כלליות:
    - כתוב תמיד בעברית, בצורה ברורה, נעימה ומקצועית.
    - אם משהו לא ברור — בקש הבהרה מהמשתמש.
    """,
    tools=[google_search],
)
