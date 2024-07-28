import requests

def fetch_data(endpoint):
    base_url = "http://oralbekov.dias19.fvds.ru/api/maps/"
    url = base_url + endpoint
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data from {url}. Status code: {response.status_code}"}

# Example usage:
taxi_data = fetch_data("taxi/")
places_data = fetch_data("places/")
specific_place_data = fetch_data("places/1/")
restaurants_data = fetch_data("restaurants/")
specific_restaurant_data = fetch_data("restaurants/1/")
city_data = fetch_data("city/")
route_data = fetch_data("route/")

# Print the fetched data
print(taxi_data)
print(places_data)
print(specific_place_data)
print(restaurants_data)
print(specific_restaurant_data)
print(city_data)
print(route_data)
