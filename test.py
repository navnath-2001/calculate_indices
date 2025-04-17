import streamlit as st
st.set_page_config(layout="wide", page_title="Vegetation Index Calculator", page_icon="🌿")

import rasterio
import numpy as np
import tempfile
import base64
from PIL import Image
import io
import os
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from streamlit_extras.colored_header import colored_header
import json  # ✅ For JS-compatible bounds

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Leaf_icon.svg/1024px-Leaf_icon.svg.png", width=100)
    st.title("Index Options")
    indices = ["NDVI", "EVI", "NDBI", "SAVI", "ARVI", "GCI", "MSAVI", "NDWI"]
    selected_index = st.selectbox("Select an Index", indices)
    st.success(f"You selected: {selected_index}")

# Title
st.markdown("""
    <style>
        .main-title {
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            color: #2e7d32;
        }
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            text-align: center;
            color: #aaa;
            font-size: 0.8rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🌿 Vegetation Indices Calculator 🌿</div>", unsafe_allow_html=True)

# Required bands
required_bands = {
    "NDVI": ["Red", "NIR"],
    "EVI": ["Red", "NIR", "Blue"],
    "NDBI": ["SWIR", "NIR"],
    "SAVI": ["Red", "NIR"],
    "ARVI": ["Red", "NIR", "Blue"],
    "GCI": ["Green", "NIR"],
    "MSAVI": ["Red", "NIR"],
    "NDWI": ["Green", "NIR"]
}

colored_header(label="📂 Upload Required Bands", description="Upload the spectral bands required for the selected index.", color_name="green-70")

uploaded_bands = {}
for band in required_bands[selected_index]:
    uploaded_bands[band.lower()] = st.file_uploader(f"Upload {band} Band (.tif)", type=["tif", "tiff"], key=band.lower())

# Index calculation functions
def calculate_ndvi(nir, red):
    return (nir - red) / (nir + red + 1e-10)

def calculate_evi(nir, red, blue):
    return 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)

def calculate_ndbi(swir, nir):
    return (swir - nir) / (swir + nir + 1e-10)

def calculate_savi(nir, red, L=0.5):
    return ((nir - red) / (nir + red + L)) * (1 + L)

def calculate_arvi(nir, red, blue):
    return (nir - (2 * red - blue)) / (nir + (2 * red - blue) + 1e-10)

def calculate_gci(nir, green):
    return (nir / (green + 1e-10)) - 1

def calculate_msavi(nir, red):
    return (2 * nir + 1 - np.sqrt((2 * nir + 1)**2 - 8 * (nir - red))) / 2

def calculate_ndwi(green, nir):
    return (green - nir) / (green + nir + 1e-10)

def compute_index(index, bands):
    if index == "NDVI":
        return calculate_ndvi(bands["nir"], bands["red"])
    elif index == "EVI":
        return calculate_evi(bands["nir"], bands["red"], bands["blue"])
    elif index == "NDBI":
        return calculate_ndbi(bands["swir"], bands["nir"])
    elif index == "SAVI":
        return calculate_savi(bands["nir"], bands["red"])
    elif index == "ARVI":
        return calculate_arvi(bands["nir"], bands["red"], bands["blue"])
    elif index == "GCI":
        return calculate_gci(bands["nir"], bands["green"])
    elif index == "MSAVI":
        return calculate_msavi(bands["nir"], bands["red"])
    elif index == "NDWI":
        return calculate_ndwi(bands["green"], bands["nir"])
    else:
        return None

# Calculate button
if st.button("🚀 Calculate Index", key="calc_index_button") and all(uploaded_bands.values()):
    try:
        bands_data = {}
        for name, file in uploaded_bands.items():
            with rasterio.open(file) as src:
                bands_data[name] = src.read(1).astype(float)
                meta = src.meta.copy()
                bounds = src.bounds

        result = compute_index(selected_index, bands_data)

        if result is not None:
            norm_result = (result - np.nanmin(result)) / (np.nanmax(result) - np.nanmin(result))
            colormap = plt.get_cmap('viridis')
            rgba_img = (colormap(norm_result)[:, :, :3] * 255).astype(np.uint8)
            image = Image.fromarray(rgba_img)

            # Convert to base64 PNG
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            image_url = f"data:image/png;base64,{img_base64}"

            image_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]

            # Inject into map.html
            with open("map.html", "r", encoding="utf-8") as f:
                map_html = f.read()

            overlay_script = f"""
            <script>
              window.overlayData = {{
                image: "{image_url}",
                bounds: {json.dumps(image_bounds)}
              }};
            </script>
            """

            full_html = overlay_script + map_html
            components.html(full_html, height=600, scrolling=False)

            # GeoTIFF download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
                meta.update(dtype='float32', count=1, compress='lzw')
                with rasterio.open(tmp_file.name, 'w', **meta) as dst:
                    dst.write(result.astype(np.float32), 1)

                with open(tmp_file.name, 'rb') as f:
                    st.download_button(
                        label="💾 Download GeoTIFF",
                        data=f,
                        file_name=f"{selected_index}_result.tif",
                        mime="image/tiff"
                    )
        else:
            st.error("❌ Selected index not implemented.")
    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")

st.markdown("<div class='footer'>© 2025 Vegetation Index App by You. All rights reserved.</div>", unsafe_allow_html=True)
