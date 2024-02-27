import streamlit as st
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape as reportlab_landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from pathlib import Path
import os

# Set a theme for the app
st.set_page_config(layout="wide", page_title="PDF Label Generator")

def calculate_layout(page_settings, label_info):
    # Convert margins to points for consistency
    margins = {key: value * mm for key, value in page_settings['margins'].items()}
    # Calculate available page spaces
    available_width = page_settings['page_size'][0] - (margins['left'] + margins['right'])
    available_height = page_settings['page_size'][1] - (margins['top'] + margins['bottom'])
    # Calculate label size if not provided
    if 'dimensions' not in label_info:
        label_width = available_width / label_info['columns']
        label_height = available_height / label_info['rows']
        label_info['dimensions'] = (label_width / mm, label_height / mm)  # Convert back to mm for readability
    else:
        label_width, label_height = label_info['dimensions']
        label_width *= mm  # Convert to points
        label_height *= mm  # Convert to points
    # Calculate spacing between labels
    space_between_labels_x = (available_width - (label_width * label_info['columns'])) / max((label_info['columns'] - 1), 1)
    space_between_labels_y = (available_height - (label_height * label_info['rows'])) / max((label_info['rows'] - 1), 1)
    # Check if labels fit on the page
    if label_width > available_width or label_height > available_height:
        raise ValueError("Label dimensions are too large for the page size and margins provided.")
    return {'label_width': label_width, 'label_height': label_height, 'space_x': space_between_labels_x, 'space_y': space_between_labels_y}

def create_pdf_labels(page_settings, label_info, layout, output_file):
    c = canvas.Canvas(output_file, pagesize=page_settings['page_size'])
    label_image = ImageReader(label_info['path'])
    for row in range(label_info['rows']):
        for col in range(label_info['columns']):
            x = page_settings['margins']['left'] * mm + col * (layout['label_width'] + layout['space_x'])
            y = page_settings['page_size'][1] - (page_settings['margins']['top'] * mm + (row + 1) * layout['label_height'] + row * layout['space_y'])
            c.drawImage(label_image, x, y, width=layout['label_width'], height=layout['label_height'], preserveAspectRatio=True)
    c.save()
    return output_file

def main():
    # Create a sidebar for user input
    page_size = st.sidebar.selectbox("Page Size:", ['A4', 'Letter', 'Legal', 'Custom'])
    page_size_display = page_size  # For display in filename
    if page_size == 'Custom':
        width = st.sidebar.number_input("Page Width (mm):", min_value=1, step=1)
        height = st.sidebar.number_input("Page Height (mm):", min_value=1, step=1)
        page_size = (width * mm, height * mm)  # Convert mm to points
        page_size_display = 'Custom'  # Simplified display name for custom size
    else:
        page_size_dict = {'A4': A4, 'Letter': (8.5 * 25.4 * mm, 11 * 25.4 * mm), 'Legal': (8.5 * 25.4 * mm, 14 * 25.4 * mm)}
        page_size = page_size_dict[page_size]

    orientation = st.sidebar.radio("Page Orientation:", ('Portrait', 'Landscape'))
    if orientation == 'Landscape':
        page_size = reportlab_landscape(page_size)

    # Margins
    top_margin = st.sidebar.number_input("Top Margin (mm):", min_value=0, step=1)
    bottom_margin = st.sidebar.number_input("Bottom Margin (mm):", min_value=0, step=1)
    left_margin = st.sidebar.number_input("Left Margin (mm):", min_value=0, step=1)
    right_margin = st.sidebar.number_input("Right Margin (mm):", min_value=0, step=1)

    # Label settings
    label_files = st.sidebar.file_uploader("Label Files (PNG or JPG):", accept_multiple_files=True)
    label_rows = st.sidebar.number_input("Number of Rows:", min_value=1, step=1)
    label_columns = st.sidebar.number_input("Number of Columns:", min_value=1, step=1)
    label_dimensions = st.sidebar.text_input("Label Dimensions (width x height in mm) [optional]:")

    if st.sidebar.button('Process', key="process_button", kwargs={'style': 'background-color: orange; color: white;'}):
        if label_files is not None:
            for label_file in label_files:
                # Convert uploaded file to an image
                label_image_path = Path(label_file.name)
                with open(label_image_path, "wb") as f:
                    f.write(label_file.getbuffer())

                # Prepare page and label settings
                page_settings = {'page_size': page_size, 'margins': {'top': top_margin, 'bottom': bottom_margin, 'left': left_margin, 'right': right_margin}, 'orientation': orientation}
                label_info = {'path': str(label_image_path), 'rows': label_rows, 'columns': label_columns}
                if label_dimensions:
                    width, height = map(float, label_dimensions.split('x'))
                    label_info['dimensions'] = (width, height)

                # Calculate layout and create PDF
                try:
                    layout = calculate_layout(page_settings, label_info)
                    quantity = label_rows * label_columns
                    output_filename = f"{label_image_path.stem}-{page_size_display.lower()}-{quantity}.pdf"
                    output_file = create_pdf_labels(page_settings, label_info, layout, output_filename)
                    st.success(f"PDF generated successfully for {label_file.name}!")
                    st.download_button("Download PDF", data=open(output_file, "rb").read(), file_name=output_filename)
                except Exception as e:
                    st.error(f"Error processing {label_file.name}: {e}")
        else:
            st.error("Please upload at least one label file.")

if __name__ == "__main__":
    main()
