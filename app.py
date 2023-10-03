import mysql.connector
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from bottle import Bottle, route, run, template, request, static_file
import os
import folium
app = Bottle()

def fetch_data_from_database():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='crops'
    )
    query = "SELECT Crop, Crop_Year, Season, State, Area, Production, Annual_Rainfall, Fertilizer, Pesticide, Yield FROM crop_yield"
    data = pd.read_sql_query(query, connection)
    connection.close()
    return data

def train_linear_regression_model(data):
    X = data[['Crop_Year', 'Area', 'Annual_Rainfall', 'Fertilizer', 'Pesticide']]
    y = data['Yield']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

import base64
def perform_data_analysis(data, selected_state, area_min, area_max, rainfall_min, rainfall_max, pesticides_min, pesticides_max):
    if selected_state:
        data = data[data['State'] == selected_state]
    if area_min:
        data = data[data['Area'] >= int(area_min)]
    if area_max:
        data = data[data['Area'] <= int(area_max)]
    if rainfall_min:
        data = data[data['Annual_Rainfall'] >= int(rainfall_min)]
    if rainfall_max:
        data = data[data['Annual_Rainfall'] <= int(rainfall_max)]
    if pesticides_min:
        data = data[data['Pesticide'] >= int(pesticides_min)]
    if pesticides_max:
        data = data[data['Pesticide'] <= int(pesticides_max)]
    avg_yield_by_crop = data.groupby('Crop')['Yield'].mean().reset_index()
    plt.figure(figsize=(10, 6))
    plt.bar(avg_yield_by_crop['Crop'], avg_yield_by_crop['Yield'])
    plt.xlabel('Crop')
    plt.ylabel('Average Yield')
    plt.title('Average Crop Yield by Crop')
    plt.xticks(rotation=90)
    plt.tight_layout()
    temp_filename = 'my_plot.png'  
    plt.savefig(temp_filename, format='png')
    with open(temp_filename, 'rb') as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()
    analysis_results = f"<h2>Analysis Results</h2>" \
                       f"<p>Average Yield by Crop:</p>" \
                       f"<img src='data:image/png;base64,{img_base64}' />"
    os.remove(temp_filename)
    return analysis_results

#routing
@app.route('/')
def index():
    return template('views/index.html')

@app.route('/yield', method='GET')
def yield_prediction():
    data = fetch_data_from_database()
    crop_list = data['Crop'].unique()
    selected_crop = request.query.get('crop')
    if selected_crop:
        filtered_data = data[data['Crop'] == selected_crop]
        model = train_linear_regression_model(filtered_data)
        predictions = model.predict(filtered_data[['Crop_Year', 'Area', 'Annual_Rainfall', 'Fertilizer', 'Pesticide']])
        plt.figure(figsize=(10, 5))
        plt.plot(filtered_data['Crop_Year'], filtered_data['Yield'], label='Actual Yield', marker='o')
        plt.plot(filtered_data['Crop_Year'], predictions, label='Predicted Yield', marker='x')
        plt.xlabel('Crop Year')
        plt.ylabel('Yield')
        plt.title(f'Yield Prediction for {selected_crop}')
        plt.legend()
        plt.grid(True)
        yield_chart_filename = f"yield_chart_{selected_crop}.png"
        plt.savefig(f'static/images/{yield_chart_filename}')
        return template('views/yield.html', selected_crop=selected_crop, yield_chart=yield_chart_filename, crop_list=crop_list)
    return template('views/yield.html', selected_crop=None, yield_chart=None, crop_list=crop_list)

@app.route('/analysis', method='GET')
def analysis():
    data = fetch_data_from_database()
    states = data["State"].unique()
    selected_state = request.query.get('state')
    area_min = request.query.get('area_min')
    area_max = request.query.get('area_max')
    rainfall_min = request.query.get('rainfall_min')
    rainfall_max = request.query.get('rainfall_max')
    pesticides_min = request.query.get('pesticides_min')
    pesticides_max = request.query.get('pesticides_max')
    analysis_results = perform_data_analysis(data, selected_state, area_min, area_max, rainfall_min, rainfall_max, pesticides_min, pesticides_max)
    return template('analysis.html', results=analysis_results, selected_state=selected_state, states=states)  # Pass 'states' variable to the template
   
@app.route('/mapping', method='GET')
def indian_map():
    data = fetch_data_from_database()
    top_crops_by_state = data.groupby("State").apply(lambda group: group.nlargest(3, "Yield")).reset_index(drop=True)
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    states = [{"name": "Andhra Pradesh", "coords": [15.9129, 79.7400]},
    {"name": "Arunachal Pradesh", "coords": [27.1004, 93.6167]},
    {"name": "Assam", "coords": [26.2006, 92.9376]},
    {"name": "Bihar", "coords": [25.0961, 85.3131]},
    {"name": "Chhattisgarh", "coords": [21.2787, 81.8661]},
    {"name": "Delhi", "coords": [28.6139, 77.2090]},
    {"name": "Goa", "coords": [15.2993, 74.1240]},
    {"name": "Gujarat", "coords": [22.2587, 71.1924]},
    {"name": "Haryana", "coords": [29.0588, 76.0856]},
    {"name": "Himachal Pradesh", "coords": [31.1048, 77.1734]},
    {"name": "Jammu and Kashmir", "coords": [33.2778, 75.3412]},
    {"name": "Jharkhand", "coords": [23.6102, 85.2799]},
    {"name": "Karnataka", "coords": [15.3173, 75.7139]},
    {"name": "Kerala", "coords": [10.8505, 76.2711]},
    {"name": "Madhya Pradesh", "coords": [22.9734, 78.6569]},
    {"name": "Maharashtra", "coords": [19.7515, 75.7139]},
    {"name": "Manipur", "coords": [24.6637, 93.9063]},
    {"name": "Meghalaya", "coords": [25.4670, 91.3662]},
    {"name": "Mizoram", "coords": [23.6850, 92.9376]},
    {"name": "Nagaland", "coords": [26.1584, 94.5624]},
    {"name": "Odisha", "coords": [20.9517, 85.0985]},
    {"name": "Puducherry", "coords": [11.9416, 79.8083]},
    {"name": "Punjab", "coords": [31.1471, 75.3412]},
    {"name": "Tamil Nadu", "coords": [11.1271, 78.6569]},
    {"name": "Telangana", "coords": [18.1124, 79.0193]},
    {"name": "Tripura", "coords": [23.9408, 91.9882]},
    {"name": "Uttar Pradesh", "coords": [26.8467, 80.9462]},
    {"name": "Uttarakhand", "coords": [30.0668, 79.0193]},
    {"name": "West Bengal", "coords": [22.9868, 87.8550]} ]
    popup_width = 175
    popup_height = 100
    state_crops_info = {}
    for state in states:
        state_name = state["name"]
        state_crops = top_crops_by_state[top_crops_by_state["State"] == state_name]
        unique_crops = []
        for index, row in state_crops.iterrows():
            crop_name = row["Crop"]
            crop_yield = row["Yield"]
            if crop_name not in [crop["name"] for crop in unique_crops]:
                unique_crops.append({"name": crop_name, "yield": crop_yield})
        popup_content = f"<div style='width: {popup_width}px; height: {popup_height}px;'><h3>{state_name}</h3><ul>"
        for crop in unique_crops:
            popup_content += f"<li><b>{crop['name']}: {crop['yield']}</b></li>"
        popup_content += "</ul></div>"
        state_crops_info[state_name] = popup_content
    for state in states:
        state_name = state["name"]
        popup_content = state_crops_info[state_name]
        folium.Marker(location=state["coords"], popup=popup_content).add_to(m)
    m.save("indian_map.html")
    with open("indian_map.html", "r") as f:
        map_html = f.read()
    return map_html

@app.route('/static/images/<filename>')
def serve_image(filename):
    return static_file(filename, root='./static/images')

@route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='./static')
    
if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)
