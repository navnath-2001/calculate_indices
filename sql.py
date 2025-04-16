import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw

st.title("Interactive Map - Show Selected Coordinates")

# Create a map
m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

# Add drawing tools
Draw(export=True, draw_options={
    'polyline': False,
    'rectangle': True,
    'polygon': True,
    'circle': False,
    'marker': True,
    'circlemarker': False
}).add_to(m)

# Display map
map_data = st_folium(m, height=500, width=700)

# Check for drawn feature
if map_data and "last_drawn_feature" in map_data:
    feature = map_data["last_drawn_feature"]
    geometry = feature["geometry"]
    geom_type = geometry["type"]
    coords = geometry["coordinates"]

    # Display info in sidebar or below map
    st.subheader("🧭 Selected Coordinates")
    st.json(geometry)

    # Recreate selected feature with popup to show coordinates on map
    m2 = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

    if geom_type == "Point":
        lat, lon = coords[1], coords[0]
        folium.Marker(
            location=[lat, lon],
            popup=f"Lat: {lat:.6f}, Lon: {lon:.6f}",
            tooltip="Selected Point"
        ).add_to(m2)

    elif geom_type == "Polygon":
        # Extract outer ring
        polygon_coords = [[lat, lon] for lon, lat in coords[0]]
        center_lat = sum([pt[0] for pt in polygon_coords]) / len(polygon_coords)
        center_lon = sum([pt[1] for pt in polygon_coords]) / len(polygon_coords)

        folium.Polygon(
            locations=polygon_coords,
            color="blue",
            fill=True,
            fill_opacity=0.3,
            popup=f"Polygon with {len(polygon_coords)} points",
            tooltip="Polygon Area"
        ).add_to(m2)

        folium.Marker(
            location=[center_lat, center_lon],
            icon=folium.DivIcon(html=f"""<div style='font-size: 12px; color: red;'>
                {[(round(lat, 4), round(lon, 4)) for lat, lon in polygon_coords]}
            </div>""")
        ).add_to(m2)

    # Show updated map with annotations
    st.subheader("📍 Selected Geometry with Coordinates")
    st_folium(m2, height=500, width=700)
