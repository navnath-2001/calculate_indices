import streamlit as st
import rasterio
import numpy as np
import matplotlib.pyplot as plt

st.title("Vegetation Indices Calculator")

# Index options
indices = ["NDVI", "EVI", "NDBI", "SAVI", "ARVI", "GCI", "MSAVI", "NDWI"]
selected_index = st.selectbox("Select an Index", indices)
st.success(f"You selected: {selected_index}")

# Define required bands per index
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

# Upload required bands dynamically
uploaded_bands = {}
for band in required_bands[selected_index]:
    uploaded_bands[band.lower()] = st.file_uploader(f"Upload {band} Band (.tif)", type=["tif", "tiff"], key=band.lower())

# Show file status
if all(uploaded_bands[band.lower()] for band in required_bands[selected_index]):
    st.success("All required bands uploaded.")
else:
    st.info("Please upload all required bands.")

# Example for NDVI (extendable to all indices)
def calculate_ndvi(nir, red):
    return (nir - red) / (nir + red + 1e-10)

def calculate_evi(nir, red, blue):
    # Coefficients: G=2.5, C1=6, C2=7.5, L=1
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

# if st.button("Calculate Index") and all(uploaded_bands.values()):
# if st.button("Calculate Index", key="calc_index_button") and all(uploaded_bands.values()):

if st.button("Calculate Index", key="calc_index_button") and all(uploaded_bands.values()):
    try:
        # Step 1: Read raster bands into arrays
        bands_data = {}
        for name, file in uploaded_bands.items():
            with rasterio.open(file) as src:
                bands_data[name] = src.read(1).astype(float)

        # Step 2: Calculate the selected index
        result = compute_index(selected_index, bands_data)

        if result is not None:
            st.subheader(f"{selected_index} Result")

            # Step 3: Show index as map
            fig, ax = plt.subplots()
            ax.imshow(result, cmap="viridis")
            ax.axis("off")
            st.pyplot(fig)

            # Step 4: Show values as a table (optional - show only sample for performance)
            st.subheader("Sample Pixel Values")
            # You can limit to 10x10 just to avoid huge table
            sample = result[:10, :10]
            st.dataframe(sample)

            # Step 5: Save and provide download
            with rasterio.open(list(uploaded_bands.values())[0]) as src:
                profile = src.profile
            profile.update(dtype='float32', count=1, compress='lzw')

            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tif") as tmp_file:
                with rasterio.open(tmp_file.name, 'w', **profile) as dst:
                    dst.write(result.astype(np.float32), 1)

                with open(tmp_file.name, 'rb') as f:
                    st.download_button(
                        label="Download GeoTIFF",
                        data=f,
                        file_name=f"{selected_index}_result.tif",
                        mime="image/tiff"
                    )

        else:
            st.error("Selected index not implemented.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")

# fig, ax = plt.subplots()
# result = np.random.rand(100, 100)

# im = ax.imshow(result, cmap="viridis")
# ax.set_title("Index Map")
# ax.axis("off")
# fig.colorbar(im, ax=ax, orientation="horizontal", shrink=0.7)
# st.pyplot(fig)      
im = ax.imshow(result, cmap="viridis")
fig, ax = plt.subplots()
ax.axis("off")
fig.colorbar(im, ax=ax, orientation="horizontal", shrink=0.7)
st.pyplot(fig)


