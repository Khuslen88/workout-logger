#!/usr/bin/env python3
"""
Workout Logger - Track exercises, meals, and progress
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional

# Data file paths
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
WORKOUT_FILE = os.path.join(DATA_DIR, "workouts.json")
MEALS_FILE = os.path.join(DATA_DIR, "meals.json")
CUSTOM_FOODS_FILE = os.path.join(DATA_DIR, "custom_foods.json")
TEMPLATES_FILE = os.path.join(DATA_DIR, "templates.json")

# Body part categories with suggested exercises
BODY_PARTS = {
    "chest": ["Bench Press", "Push-ups", "Dumbbell Fly", "Incline Press", "Cable Crossover"],
    "back": ["Pull-ups", "Deadlift", "Barbell Row", "Lat Pulldown", "Seated Row"],
    "shoulders": ["Overhead Press", "Lateral Raise", "Front Raise", "Face Pull", "Shrugs"],
    "arms": ["Bicep Curl", "Tricep Dip", "Hammer Curl", "Skull Crusher", "Cable Pushdown"],
    "core": ["Plank", "Crunches", "Leg Raise", "Russian Twist", "Mountain Climbers"],
    "legs": ["Squat", "Lunges", "Leg Press", "Calf Raise", "Romanian Deadlift"],
}

# Word to number mapping for input flexibility
WORD_TO_NUMBER = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# Expanded calorie database (per 100g unless noted)
CALORIE_DATABASE = {
    # Proteins
    "chicken breast": 165, "chicken thigh": 209, "beef": 250, "ground beef": 332,
    "salmon": 208, "tuna": 132, "shrimp": 99, "eggs": 155, "egg whites": 52,
    "tofu": 76, "turkey": 135, "pork": 242,
    # Carbs
    "rice": 130, "brown rice": 123, "bread": 265, "whole wheat bread": 247,
    "pasta": 131, "oatmeal": 68, "potato": 77, "sweet potato": 86, "quinoa": 120,
    # Vegetables
    "broccoli": 34, "spinach": 23, "carrot": 41, "tomato": 18, "cucumber": 16,
    "bell pepper": 31, "lettuce": 15, "onion": 40, "mushroom": 22, "avocado": 160,
    # Fruits
    "banana": 89, "apple": 52, "orange": 47, "strawberry": 32, "blueberry": 57,
    "grapes": 69, "watermelon": 30, "mango": 60,
    # Dairy
    "milk": 42, "almond milk": 15, "yogurt": 59, "greek yogurt": 97,
    "cheese": 402, "cottage cheese": 98,
    # Snacks & Other
    "protein shake": 120, "protein bar": 200, "almonds": 579, "peanut butter": 588,
    "honey": 304, "olive oil": 884,
}


def load_data(filepath: str) -> list:
    """Load data from JSON file."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []


def load_dict_data(filepath: str) -> dict:
    """Load dictionary data from JSON file."""
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}


def save_data(filepath: str, data) -> None:
    """Save data to JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def display_menu():
    """Display the main menu."""
    print("\n" + "=" * 50)
    print("         💪 WORKOUT LOGGER 💪")
    print("=" * 50)
    print("\n  1. Start Workout Session")
    print("  2. Load Workout Template")
    print("  3. Log Meal")
    print("  4. View Workout History")
    print("  5. View Progress & PRs")
    print("  6. View Weekly Summary")
    print("  7. View Today's Calories")
    print("  8. Exit")
    print("\n" + "-" * 50)


# =============================================================================
# PR TRACKER
# =============================================================================

def parse_weight(weight_str: str) -> Optional[float]:
    """Parse weight string to float (handles kg and lbs)."""
    if not weight_str:
        return None
    weight_str = weight_str.lower().strip()
    try:
        if "kg" in weight_str:
            return float(weight_str.replace("kg", "").strip())
        elif "lb" in weight_str:
            return float(weight_str.replace("lbs", "").replace("lb", "").strip()) * 0.453592
        else:
            return float(weight_str)
    except ValueError:
        return None


def get_pr_for_exercise(exercise: str) -> Optional[dict]:
    """Get the personal record for an exercise."""
    workouts = load_data(WORKOUT_FILE)
    exercise_workouts = [w for w in workouts if w["exercise"].lower() == exercise.lower()]

    if not exercise_workouts:
        return None

    best = None
    best_weight = 0

    for w in exercise_workouts:
        weight = parse_weight(w.get("weight", ""))
        if weight and weight > best_weight:
            best_weight = weight
            best = w

    return best


def check_pr(exercise: str, new_weight: str) -> tuple:
    """Check if new weight is a PR. Returns (is_pr, old_pr_weight)."""
    new_weight_val = parse_weight(new_weight)
    if not new_weight_val:
        return False, None

    old_pr = get_pr_for_exercise(exercise)
    if not old_pr:
        return True, None  # First time doing this exercise with weight

    old_weight = parse_weight(old_pr.get("weight", ""))
    if old_weight and new_weight_val > old_weight:
        return True, old_pr.get("weight")

    return False, None


# =============================================================================
# REST TIMER
# =============================================================================

def rest_timer(seconds: int = 90):
    """Countdown rest timer between sets."""
    print(f"\n⏱️  Rest Timer: {seconds} seconds")
    print("   Press Ctrl+C to skip\n")

    try:
        for remaining in range(seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer_display = f"   ⏳ {mins:01d}:{secs:02d} remaining..."
            print(f"\r{timer_display}", end="", flush=True)
            time.sleep(1)
        print("\r   🔔 TIME'S UP! Get back to work! 💪      ")
    except KeyboardInterrupt:
        print("\r   ⏭️  Timer skipped                        ")


# =============================================================================
# PROGRESS VIEW
# =============================================================================

def view_progress():
    """View progress charts and PRs for exercises."""
    print("\n" + "=" * 50)
    print("         📈 PROGRESS & PRs")
    print("=" * 50)

    workouts = load_data(WORKOUT_FILE)
    if not workouts:
        print("\nNo workouts logged yet!")
        return

    # Get unique exercises with weights
    exercises_with_weights = {}
    for w in workouts:
        ex = w["exercise"]
        weight = parse_weight(w.get("weight", ""))
        if weight:
            if ex not in exercises_with_weights:
                exercises_with_weights[ex] = []
            exercises_with_weights[ex].append({
                "weight": weight,
                "date": w["date"],
                "sets": w["sets"],
                "reps": w["reps"]
            })

    if not exercises_with_weights:
        print("\nNo weighted exercises logged yet!")
        return

    # Show PRs for each exercise
    print("\n🏆 PERSONAL RECORDS:")
    print("-" * 50)

    for exercise, records in sorted(exercises_with_weights.items()):
        best = max(records, key=lambda x: x["weight"])
        print(f"  {exercise:20} : {best['weight']:.1f}kg ({best['sets']}x{best['reps']}) on {best['date'][:10]}")

    # Show progress chart for selected exercise
    print("\n" + "-" * 50)
    print("\nSelect exercise to view progress chart:")
    exercises = list(exercises_with_weights.keys())
    for i, ex in enumerate(exercises, 1):
        print(f"  {i}. {ex}")
    print(f"  {len(exercises) + 1}. Back to menu")

    try:
        choice = int(input("\nChoice: "))
        if 1 <= choice <= len(exercises):
            show_progress_chart(exercises[choice - 1], exercises_with_weights[exercises[choice - 1]])
    except ValueError:
        pass


def show_progress_chart(exercise: str, records: list):
    """Show ASCII progress chart for an exercise."""
    print(f"\n📊 Progress Chart: {exercise}")
    print("-" * 50)

    # Sort by date
    sorted_records = sorted(records, key=lambda x: x["date"])

    if len(sorted_records) < 2:
        print("  Need at least 2 records to show progress")
        return

    # Get weight range
    weights = [r["weight"] for r in sorted_records]
    min_w, max_w = min(weights), max(weights)
    weight_range = max_w - min_w if max_w != min_w else 1

    # Show last 10 records
    recent = sorted_records[-10:]
    chart_height = 8

    print(f"\n  {max_w:>6.1f}kg ┤")

    for row in range(chart_height - 1, -1, -1):
        threshold = min_w + (weight_range * row / (chart_height - 1))
        line = "         │"
        for r in recent:
            if r["weight"] >= threshold:
                line += " █ "
            else:
                line += "   "
        print(line)

    print(f"  {min_w:>6.1f}kg ┤" + "───" * len(recent))

    # Date labels
    date_line = "           "
    for r in recent:
        date_line += r["date"][5:10] + " "
    print(date_line)

    # Progress summary
    first_weight = sorted_records[0]["weight"]
    last_weight = sorted_records[-1]["weight"]
    diff = last_weight - first_weight
    print(f"\n  📈 Progress: {first_weight:.1f}kg → {last_weight:.1f}kg ({'+' if diff >= 0 else ''}{diff:.1f}kg)")


# =============================================================================
# WORKOUT TEMPLATES
# =============================================================================

def load_templates() -> dict:
    """Load workout templates."""
    return load_dict_data(TEMPLATES_FILE)


def save_template(name: str, muscles: list, exercises: list):
    """Save a workout as a template."""
    templates = load_templates()
    templates[name] = {
        "muscles": muscles,
        "exercises": exercises,
        "created": datetime.now().strftime("%Y-%m-%d")
    }
    save_data(TEMPLATES_FILE, templates)


def use_template():
    """Load and use a workout template."""
    print("\n" + "=" * 50)
    print("         📋 WORKOUT TEMPLATES")
    print("=" * 50)

    templates = load_templates()

    if not templates:
        print("\nNo templates saved yet!")
        print("Complete a workout session and save it as a template.")
        return None

    print("\n📋 Your Templates:")
    template_names = list(templates.keys())
    for i, name in enumerate(template_names, 1):
        t = templates[name]
        muscle_str = " + ".join([m.title() for m in t["muscles"]])
        print(f"  {i}. {name} ({muscle_str}) - {len(t['exercises'])} exercises")
    print(f"  {len(template_names) + 1}. Cancel")

    try:
        choice = int(input("\nChoice: "))
        if 1 <= choice <= len(template_names):
            return templates[template_names[choice - 1]]
    except ValueError:
        pass

    return None


# =============================================================================
# WEEKLY SUMMARY
# =============================================================================

def view_weekly_summary():
    """View weekly workout and nutrition summary."""
    print("\n" + "=" * 50)
    print("         📅 WEEKLY SUMMARY")
    print("=" * 50)

    today = datetime.now()
    week_ago = today - timedelta(days=7)
    week_ago_str = week_ago.strftime("%Y-%m-%d")

    # Load workout data
    workouts = load_data(WORKOUT_FILE)
    week_workouts = [w for w in workouts if w["date"][:10] >= week_ago_str]

    # Load meal data
    meals = load_data(MEALS_FILE)
    week_meals = [m for m in meals if m["date"] >= week_ago_str]

    print(f"\n📆 Last 7 days ({week_ago_str} to {today.strftime('%Y-%m-%d')})")
    print("-" * 50)

    # Workout stats
    print("\n🏋️ WORKOUTS:")
    if week_workouts:
        # Count sessions (unique dates)
        session_dates = set(w["date"][:10] for w in week_workouts)
        total_exercises = len(week_workouts)

        # Body part breakdown
        body_counts = {}
        for w in week_workouts:
            bp = w["body_part"]
            body_counts[bp] = body_counts.get(bp, 0) + 1

        print(f"  Sessions: {len(session_dates)} days")
        print(f"  Total exercises: {total_exercises}")
        print(f"\n  By body part:")
        for bp, count in sorted(body_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"    {bp.title():12} : {bar} ({count})")

        # Streak calculation
        streak = calculate_streak(workouts)
        if streak > 0:
            print(f"\n  🔥 Current streak: {streak} days!")
    else:
        print("  No workouts this week")

    # Nutrition stats
    print("\n🍽️ NUTRITION:")
    if week_meals:
        total_calories = sum(m["calories"] for m in week_meals)
        days_with_meals = len(set(m["date"] for m in week_meals))
        avg_daily = total_calories / days_with_meals if days_with_meals > 0 else 0

        print(f"  Total calories: {total_calories:,}")
        print(f"  Days logged: {days_with_meals}")
        print(f"  Daily average: {avg_daily:.0f} cal")

        # Most eaten foods
        food_counts = {}
        for m in week_meals:
            food = m["food"]
            food_counts[food] = food_counts.get(food, 0) + 1

        top_foods = sorted(food_counts.items(), key=lambda x: -x[1])[:3]
        print(f"\n  Top foods:")
        for food, count in top_foods:
            print(f"    {food.title()}: {count}x")
    else:
        print("  No meals logged this week")


def calculate_streak(workouts: list) -> int:
    """Calculate current workout streak (consecutive days)."""
    if not workouts:
        return 0

    # Get unique workout dates
    dates = sorted(set(w["date"][:10] for w in workouts), reverse=True)

    if not dates:
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Check if last workout was today or yesterday
    if dates[0] != today and dates[0] != yesterday:
        return 0

    streak = 1
    for i in range(len(dates) - 1):
        current = datetime.strptime(dates[i], "%Y-%m-%d")
        prev = datetime.strptime(dates[i + 1], "%Y-%m-%d")

        if (current - prev).days == 1:
            streak += 1
        else:
            break

    return streak


# =============================================================================
# CORE WORKOUT FUNCTIONS
# =============================================================================

def get_combo_suggestions(selected_part: str) -> list:
    """Return all body parts except the one already selected."""
    return [part for part in BODY_PARTS.keys() if part != selected_part]


def select_workout_muscles() -> list:
    """Let user select body parts for today's workout (supports combos)."""
    print("\n🔥 What are you hitting today?")
    parts = list(BODY_PARTS.keys())
    for i, part in enumerate(parts, 1):
        print(f"  {i}. {part.title()}")
    print(f"  {len(parts) + 1}. Skip")

    while True:
        try:
            choice = int(input("\nChoice (1-7): "))
            if choice == len(parts) + 1:
                return []
            if 1 <= choice <= len(parts):
                selected = [parts[choice - 1]]
                break
            print("Please enter 1-7")
        except ValueError:
            print("Please enter a number")

    suggestions = get_combo_suggestions(selected[0])

    print(f"\n💪 Add combo with {selected[0].title()}?")
    for i, part in enumerate(suggestions, 1):
        print(f"  {i}. + {part.title()}")
    print(f"  {len(suggestions) + 1}. {selected[0].title()} only")

    while True:
        try:
            combo_choice = int(input("\nChoice: "))
            if combo_choice == len(suggestions) + 1:
                break
            if 1 <= combo_choice <= len(suggestions):
                selected.append(suggestions[combo_choice - 1])
                break
            print(f"Please enter 1-{len(suggestions) + 1}")
        except ValueError:
            print("Please enter a number")

    return selected


def get_exercises_for_muscles(muscles: list) -> list:
    """Get combined exercise list for selected muscles."""
    exercises = []
    for muscle in muscles:
        exercises.extend([(ex, muscle) for ex in BODY_PARTS[muscle]])
    return exercises


def parse_number(value: str) -> Optional[int]:
    """Parse a number from string - accepts digits or words like 'four'."""
    value = value.strip().lower()
    try:
        return int(value)
    except ValueError:
        pass
    if value in WORD_TO_NUMBER:
        return WORD_TO_NUMBER[value]
    return None


def collect_workout_details() -> tuple:
    """Collect sets, reps, weight, and notes from user input."""
    while True:
        sets_input = input("Sets: ").strip()
        sets = parse_number(sets_input)
        if sets is not None and sets > 0:
            break
        print("Please enter a valid number (e.g., 3 or 'three')")

    while True:
        reps_input = input("Reps: ").strip()
        reps = parse_number(reps_input)
        if reps is not None and reps > 0:
            break
        print("Please enter a valid number (e.g., 10 or 'ten')")

    weight = input("Weight (optional, e.g., 60kg): ").strip()
    notes = input("Notes (optional): ").strip()

    return (sets, reps, weight, notes)


def log_workout(template: dict = None):
    """Log a full workout session with multiple exercises."""
    print("\n" + "=" * 50)
    print("         🏋️ WORKOUT SESSION")
    print("=" * 50)

    if template:
        muscles = template["muscles"]
        template_exercises = template["exercises"]
        print(f"\n📋 Loading template with {len(template_exercises)} exercises")
    else:
        muscles = select_workout_muscles()
        template_exercises = None

    if not muscles:
        print("Workout skipped.")
        return

    muscle_str = " + ".join([m.title() for m in muscles])
    print(f"\n🎯 Today's focus: {muscle_str}")
    print("-" * 50)

    available = get_exercises_for_muscles(muscles)
    session_workouts = []
    exercise_count = 1

    while True:
        print(f"\n📝 Exercise #{exercise_count}")

        # Show template suggestion if available
        if template_exercises and exercise_count <= len(template_exercises):
            suggested = template_exercises[exercise_count - 1]
            print(f"   📋 Template suggests: {suggested['exercise']}")

        print("\n💡 Suggested exercises:")
        for i, (ex, muscle) in enumerate(available, 1):
            print(f"  {i}. {ex} ({muscle})")
        print(f"  {len(available) + 1}. Enter custom exercise")
        print(f"  {len(available) + 2}. ✅ Workout Done")

        while True:
            try:
                choice = int(input("\nChoice: "))
                if choice == len(available) + 2:
                    # Workout done - offer to save as template
                    if session_workouts:
                        workouts = load_data(WORKOUT_FILE)
                        workouts.extend(session_workouts)
                        save_data(WORKOUT_FILE, workouts)
                        print(f"\n🎉 Great session! Logged {len(session_workouts)} exercises.")
                        print(f"   Muscles hit: {muscle_str}")

                        # Offer to save as template
                        save_as = input("\n💾 Save as template? (y/n): ").lower()
                        if save_as == "y":
                            name = input("Template name: ").strip()
                            if name:
                                exercises_for_template = [
                                    {"exercise": w["exercise"], "body_part": w["body_part"]}
                                    for w in session_workouts
                                ]
                                save_template(name, muscles, exercises_for_template)
                                print(f"   ✅ Template '{name}' saved!")
                    return
                elif choice == len(available) + 1:
                    exercise = input("Enter exercise name: ").strip()
                    body_part = muscles[0]
                    break
                elif 1 <= choice <= len(available):
                    exercise, body_part = available[choice - 1]
                    break
                print(f"Please enter 1-{len(available) + 2}")
            except ValueError:
                print("Please enter a number")

        sets, reps, weight, notes = collect_workout_details()

        # Check for PR
        is_pr, old_pr = check_pr(exercise, weight)

        workout = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "body_part": body_part,
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "notes": notes,
            "session_muscles": muscles,
        }

        session_workouts.append(workout)
        print(f"\n✅ Logged: {exercise} - {sets}x{reps}" + (f" @ {weight}" if weight else ""))

        # Celebrate PR!
        if is_pr:
            if old_pr:
                print(f"🏆 NEW PERSONAL RECORD! Previous best: {old_pr}")
            else:
                print(f"🏆 FIRST RECORDED LIFT for {exercise}! Keep pushing!")

        print(f"   Session total: {len(session_workouts)} exercises")

        # Offer rest timer
        rest = input("\n⏱️  Start rest timer? (Enter seconds or 'n' to skip): ").strip().lower()
        if rest != 'n' and rest != '':
            try:
                seconds = int(rest) if rest else 90
                rest_timer(seconds)
            except ValueError:
                rest_timer(90)

        exercise_count += 1


# =============================================================================
# MEAL LOGGING
# =============================================================================

def log_meal():
    """Log a meal with calorie tracking."""
    print("\n" + "=" * 50)
    print("         🍽️  LOG MEAL")
    print("=" * 50)

    custom_foods = load_dict_data(CUSTOM_FOODS_FILE)
    all_foods = {**CALORIE_DATABASE, **custom_foods}

    print("\n📋 Food Database:")
    foods = list(all_foods.keys())

    for i, food in enumerate(foods, 1):
        cal = all_foods[food]
        marker = "⭐" if food in custom_foods else "  "
        print(f"  {marker}{i:2}. {food.title():20} ({cal} cal/100g)")

    print(f"\n  ⭐ = Your custom foods")
    print(f"\n  Type food number, food name, or 'done' to finish")

    meals_today = []
    new_custom_foods = {}

    while True:
        entry = input("\nFood (or 'done'): ").strip().lower()
        if entry == "done":
            break

        try:
            idx = int(entry) - 1
            if 0 <= idx < len(foods):
                food_name = foods[idx]
                calories_per_100g = all_foods[food_name]
            else:
                print("Invalid number")
                continue
        except ValueError:
            food_name = entry
            if food_name in all_foods:
                calories_per_100g = all_foods[food_name]
            else:
                try:
                    calories_per_100g = int(input(f"Calories per 100g for '{food_name}': "))
                    new_custom_foods[food_name] = calories_per_100g
                    all_foods[food_name] = calories_per_100g
                    foods.append(food_name)
                    print(f"  💾 '{food_name}' saved to your custom foods!")
                except ValueError:
                    print("Invalid calories")
                    continue

        try:
            grams = float(input(f"Grams of {food_name}: "))
            calories = int((grams / 100) * calories_per_100g)

            meal = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "food": food_name,
                "grams": grams,
                "calories": calories,
            }
            meals_today.append(meal)
            print(f"  ✅ Added: {food_name} ({grams}g) = {calories} cal")
        except ValueError:
            print("Invalid amount")

    if new_custom_foods:
        existing_custom = load_dict_data(CUSTOM_FOODS_FILE)
        existing_custom.update(new_custom_foods)
        save_data(CUSTOM_FOODS_FILE, existing_custom)

    if meals_today:
        meals = load_data(MEALS_FILE)
        meals.extend(meals_today)
        save_data(MEALS_FILE, meals)
        total = sum(m["calories"] for m in meals_today)
        print(f"\n📊 Meal logged! Total: {total} calories")


# =============================================================================
# VIEW FUNCTIONS
# =============================================================================

def view_workout_history():
    """View workout history."""
    print("\n" + "=" * 50)
    print("         📜 WORKOUT HISTORY")
    print("=" * 50)

    workouts = load_data(WORKOUT_FILE)
    if not workouts:
        print("\nNo workouts logged yet!")
        return

    print("\n  1. View all")
    print("  2. Filter by body part")

    choice = input("\nChoice: ").strip()

    if choice == "2":
        parts = list(BODY_PARTS.keys())
        print("\n📍 Select body part:")
        for i, part in enumerate(parts, 1):
            print(f"  {i}. {part.title()}")

        try:
            idx = int(input("\nChoice: ")) - 1
            if 0 <= idx < len(parts):
                body_part = parts[idx]
                workouts = [w for w in workouts if w["body_part"] == body_part]
                print(f"\n--- {body_part.title()} Workouts ---")
        except ValueError:
            print("\n--- All Workouts ---")
    else:
        print("\n--- All Workouts ---")

    if not workouts:
        print("No matching workouts found.")
        return

    for w in reversed(workouts[-10:]):
        weight_str = f" @ {w['weight']}" if w.get("weight") else ""
        notes_str = f" - {w['notes']}" if w.get("notes") else ""
        session = w.get("session_muscles", [w["body_part"]])
        session_str = " + ".join([s.title() for s in session]) if len(session) > 1 else ""

        print(f"\n  [{w['date']}] {w['body_part'].title()}" + (f" ({session_str} day)" if session_str else ""))
        print(f"    {w['exercise']}: {w['sets']}x{w['reps']}{weight_str}{notes_str}")


def view_calories():
    """View today's calorie intake."""
    print("\n" + "=" * 50)
    print("         🔥 TODAY'S CALORIES")
    print("=" * 50)

    meals = load_data(MEALS_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    today_meals = [m for m in meals if m["date"] == today]

    if not today_meals:
        print("\nNo meals logged today!")
        return

    total = 0
    print(f"\n📋 Meals on {today}:")
    for m in today_meals:
        print(f"  [{m['time']}] {m['food'].title():20} {m['grams']:>6}g = {m['calories']:>4} cal")
        total += m["calories"]

    print(f"\n  {'─' * 40}")
    print(f"  {'TOTAL':26} = {total:>4} cal")

    goal = 2000
    remaining = goal - total
    if remaining > 0:
        print(f"  {'Remaining (2000 cal goal)':26} = {remaining:>4} cal")
    else:
        print(f"  🎯 Goal reached! (+{-remaining} cal over)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main application loop."""
    while True:
        display_menu()
        choice = input("Select option (1-8): ").strip()

        if choice == "1":
            log_workout()
        elif choice == "2":
            template = use_template()
            if template:
                log_workout(template)
        elif choice == "3":
            log_meal()
        elif choice == "4":
            view_workout_history()
        elif choice == "5":
            view_progress()
        elif choice == "6":
            view_weekly_summary()
        elif choice == "7":
            view_calories()
        elif choice == "8":
            # Show streak on exit
            workouts = load_data(WORKOUT_FILE)
            streak = calculate_streak(workouts)
            if streak > 0:
                print(f"\n🔥 Current streak: {streak} days! Keep it going!")
            print("\n👋 Keep pushing! See you next workout!\n")
            break
        else:
            print("Please enter 1-8")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
