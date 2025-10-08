#import
import random
import pyfiglet
import mysql.connector
from geopy import distance


# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    database='test1',
    user='root',
    password='12345',
    autocommit=True
)

#eras(energy consumption)
ERAS = {
    'ANCIENT': 1.2,
    'MEDIEVAL': 1.1,
    'MODERN': 1.0,
    'FUTURE': 0.9
}

#get 15 random airports
def get_airports():
    sql = """SELECT ident, name, latitude_deg, longitude_deg, era
             FROM airport
             WHERE continent = 'EU' \
               AND type = 'large_airport'
             ORDER BY RAND() LIMIT 15"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    return cursor.fetchall()

#get all goals
def get_goals():
    sql = "SELECT * FROM goal"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    return cursor.fetchall()

#create a new game
def create_game(credits, player_range, location, name, airports): 
    sql = "INSERT INTO game (credits, player_range, location, screen_name) VALUES (%s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(sql, (credits, player_range, location, name))
    game_id = cursor.lastrowid

    goals = get_goals()
    goal_list = []
    for goal in goals:
        for i in range(goal['probability']):
            goal_list.append(goal['id'])

    available_airports = [ap for ap in airports if ap['ident'] != location]
    random.shuffle(available_airports)

    for i, goal_id in enumerate(goal_list):
        if i < len(available_airports):
            sql = "INSERT INTO ports (game, airport, goal) VALUES (%s, %s, %s)"
            cursor.execute(sql, (game_id, available_airports[i]['ident'], goal_id))

    return game_id
#getting airport info
def get_airport_info(icao):
    sql = "SELECT ident, name, latitude_deg, longitude_deg, era FROM airport WHERE ident = %s"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (icao,))
    return cursor.fetchone()

#checking goals
def check_goal(game_id, airport):
    sql = """SELECT g.name, g.credits
             FROM ports p
                      JOIN goal g ON p.goal = g.id
             WHERE p.game = %s \
               AND p.airport = %s"""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (game_id, airport))
    return cursor.fetchone()

#calculate distance
def calculate_distance(current, target):
    start = get_airport_info(current)
    end = get_airport_info(target)

    if not start or not end:
        return 0, 0

    base_distance = distance.distance(
        (start['latitude_deg'], start['longitude_deg']),
        (end['latitude_deg'], end['longitude_deg'])
    ).km

    era_modifier = ERAS.get(end['era'], 1.0)
    modified_distance = base_distance * era_modifier

    return base_distance, modified_distance

#airports in range
def airports_in_range(current, airports, player_range):
    in_range = []
    for airport in airports:
        if airport['ident'] == current:
            continue
        base_dist, adj_dist = calculate_distance(current, airport['ident'])
        if adj_dist <= player_range and adj_dist > 0:
            in_range.append({
                'ident': airport['ident'],
                'name': airport['name'],
                'era': airport['era'],
                'distance': adj_dist
            })
    return in_range


#update game
def update_game(game_id, location, player_range, credits, shards):
    sql = "UPDATE game SET location = %s, player_range = %s, credits = %s, chrono_shards = %s WHERE id = %s"
    cursor = conn.cursor()
    cursor.execute(sql, (location, player_range, credits, shards, game_id))

#game state
def get_game_state(game_id):
    sql = "SELECT credits, player_range, location, chrono_shards FROM game WHERE id = %s"
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (game_id,))
    return cursor.fetchone()


# MAIN GAME
big_text = pyfiglet.figlet_format("Chrono Quest")
print(big_text)
player_name = input("Enter your name: ")

START_CREDITS = 15000
START_RANGE = 2500
REQUIRED_SHARDS = 5

airports = get_airports()
start_airport = airports[0]['ident']
current_airport = start_airport

game_id = create_game(START_CREDITS, START_RANGE, start_airport, player_name, airports)

game_over = False
won = False

print(f"\nCollect {REQUIRED_SHARDS} Chrono Shards and return to start!")

while not game_over:
    airport_info = get_airport_info(current_airport)
    game_state = get_game_state(game_id)

    credits = game_state['credits']
    player_range = game_state['player_range']
    shards = game_state['chrono_shards']
    era = airport_info['era']

    print(f"\n {airport_info['name']} ({era})")
    print(f" Credits: {credits} |  Range: {player_range:.0f}km")
    print(f" Shards: {shards}/{REQUIRED_SHARDS}")

    # Check for goal
    goal = check_goal(game_id, current_airport)
    if goal:
        print(f"\n Found: {goal['name']}!")

        if goal['name'] == 'Chrono Shard':
            if shards < REQUIRED_SHARDS:
                shards += 1
                print(f" Collected Chrono Shard! ({shards}/{REQUIRED_SHARDS})")
                # Remove shard
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ports WHERE game = %s AND airport = %s", (game_id, current_airport))
        elif goal['name'] == 'Paradox Trap':
            credits = max(0, credits + goal['credits'])
            print(f" Lost {abs(goal['credits'])} credits!")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ports WHERE game = %s AND airport = %s", (game_id, current_airport))
        elif goal['name'] == 'Artifact Cache':
            credits += goal['credits']
            print(f" Gained {goal['credits']} credits!")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ports WHERE game = %s AND airport = %s", (game_id, current_airport))


        update_game(game_id, current_airport, player_range, credits, shards)

    # Win condition
    if shards >= REQUIRED_SHARDS and current_airport == start_airport:
        print(f"\n You won! All shards collected!")
        won = True
        game_over = True
        continue

    # Buy fuel
    if credits > 0:
        fuel = input(f"\n Buy energy? (1 credit = 2km). Amount or Enter to skip: ")
        destinations = airports_in_range(current_airport, airports, player_range)
        fuel_str = str(fuel)
        if fuel_str == '':
            # Show destinations


            if not destinations:
                print("\n No airports in range! Game Over!")
                game_over = True
                continue

            print(f"\n Destinations:")
            for ap in destinations:
                print(f"   {ap['ident']} - {ap['name']} ({ap['era']}) - {ap['distance']:.0f}km")
        else:
            fuel_amount = float(fuel)
            if fuel_amount <= credits:
                player_range += fuel_amount * 2
                credits -= fuel_amount
                print(f" Added {fuel_amount * 2:.0f}km range")
                update_game(game_id, current_airport, player_range, credits, shards)
            elif fuel_amount > credits:
                print(" Not enough credits!")


            elif credits <= 0:
                # Travel
                choice = input(f"\n Enter ICAO or 'Q' to quit: ").upper()

                if choice == 'Q':
                    game_over = True
                    continue

                destination_found = False
                for ap in destinations:
                    if ap['ident'] == choice:
                        player_range -= ap['distance']
                        current_airport = ap['ident']
                        update_game(game_id, current_airport, player_range, credits, shards)
                        print(f" Traveled to {ap['name']}")
                        destination_found = True
                        break

                if not destination_found:
                    print(" Invalid choice")


            else:
                print(" Invalid input")



# Game over
print(f"\n{' You won!' if won else ' Game Over'}")
final_state = get_game_state(game_id)
print(
    f"Final - Credits: {final_state['credits']}, Range: {final_state['player_range']:.0f}km, Shards: {final_state['chrono_shards']}/{REQUIRED_SHARDS}")

    

