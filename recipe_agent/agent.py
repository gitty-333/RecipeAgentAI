from google.adk.agents import Agent
from google.adk.tools import google_search

import google.generativeai as genai
import os
import re

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Detect user language (Hebrew/English) ---
def detect_language(text: str) -> str:
    """
    Returns 'he' for Hebrew, 'en' for English.
    Default = Hebrew if detection unclear.
    """
    if re.search(r"[\u0590-\u05FF]", text):
        return "he"
    return "en"


# --- Image generation with Gemini ---
def generate_recipe_image(recipe_title: str) -> str:
    """
    Creates a high-quality food image using Gemini.
    Always returns a valid URL.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-image")
        response = model.generate_images(
            prompt=f"Create a high-quality food photograph of the dish '{recipe_title}'.",
            size="1024x1024"
        )

        if response and response.generated_images:
            return response.generated_images[0].url

    except Exception:
        pass

    return "https://via.placeholder.com/600x400?text=No+Image+Available"


# --- Find 2 recipes ---
def find_recipes(ingredients: str, preference: str) -> dict:
    """
    Searches for two recipes based on ingredients + preference.
    Supports Hebrew or English queries.
    """
    lang = detect_language(ingredients + " " + preference)

    if lang == "he":
        query = f"מתכונים עם {ingredients} שמתאימים ל {preference}"
        default_title = "מתכון ללא שם"
        default_desc = "אין תיאור זמין."
    else:
        query = f"recipes with {ingredients} suitable for {preference}"
        default_title = "Unnamed recipe"
        default_desc = "No description available."

    search_results = google_search(query=query)

    if not search_results or "results" not in search_results:
        return {
            "status": "error",
            "message": "לא נמצאו מתכונים תואמים." if lang == "he" else "No matching recipes were found."
        }

    recipes = []
    for result in search_results["results"][:2]:
        recipes.append({
            "title": result.get("title", default_title),
            "snippet": result.get("snippet", default_desc),
            "link": result.get("link", "")
        })

    return {"status": "success", "recipes": recipes}


# --- Full recipe + AI image ---
def get_full_recipe(recipe_title: str) -> dict:
    """
    Returns a full recipe: instructions + AI-generated image.
    Works in both Hebrew and English.
    """
    lang = detect_language(recipe_title)

    query = (
        f"{recipe_title} מתכון מלא שלבי הכנה"
        if lang == "he"
        else f"{recipe_title} full recipe step by step"
    )

    results = google_search(query=query)

    if not results or "results" not in results or len(results["results"]) == 0:
        return {
            "status": "error",
            "message": "לא הצלחתי למצוא את פרטי המתכון." if lang == "he"
                       else "Could not find the recipe details."
        }

    recipe_data = results["results"][0]
    image_url = generate_recipe_image(recipe_title)

    return {
        "status": "success",
        "title": recipe_title,
        "instructions": recipe_data.get(
            "snippet",
            "אין הוראות זמינות." if lang == "he" else "No instructions available."
        ),
        "image_url": image_url
    }


# --- Main agent definition ---
root_agent = Agent(
    name="recipe_agent",
    model="gemini-2.0-flash",
    description="An agent that suggests 2 recipes and returns a full recipe including instructions and an AI-generated dish image.",
    instruction="""
You are a smart and professional cooking assistant.
Your purpose is to help the user find recipes based on available ingredients,
match them to the user's preferences, and provide a full recipe including an AI-generated image.

IMPORTANT:
- You must reply in the SAME LANGUAGE the user used (Hebrew or English).
- If anything is unclear, ask the user for clarification.

Workflow:

1. The user gives a list of ingredients they have.

2. Ask the user:
   Hebrew: "האם יש לך העדפות למתכון? לדוגמה: קר / חם / מהיר / קל / פרווה / חלבי / חריף / בריא / לא משנה."
   English: "Do you have any recipe preferences? For example: cold / hot / quick / easy / dairy-free / spicy / healthy / doesn't matter."

3. After the user responds:
   Call: find_recipes(ingredients, preference)
   Then present two matching recipes: title + short description.

4. Ask the user:
   Hebrew: "איזה מתכון תרצה שאביא עבורך במלואו?"
   English: "Which recipe would you like me to provide in full?"

5. When the user chooses:
   Call: get_full_recipe(recipe_title)

6. Return to the user:
   • Dish name  
   • Preparation instructions  
   • AI-generated food image (if allowed by the platform)

General rules:
- Always reply in a clear, pleasant, professional tone.
- Always mirror the user's language (Hebrew or English).
""",
    tools=[google_search],
)
