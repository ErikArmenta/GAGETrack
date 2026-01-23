# -*- coding: utf-8 -*-
"""
Created on Tue Jan 20 06:51:57 2026

@author: acer
"""


import streamlit as st

import qrcode
from io import BytesIO

# Page settings
st.set_page_config(page_title="QR Code Generator", page_icon="🔳", layout="centered")

# Title
st.title("🔳 QR Code Generator")
st.write("Create your own QR codes instantly. Enter text, a link, or any data below.")

# User input
data = st.text_input("Enter the content for your QR Code:")

# Customization options
st.subheader("⚙️ Customization")
col1, col2 = st.columns(2)

with col1:
    fill_color = st.color_picker("QR Color", "#000000")
with col2:
    back_color = st.color_picker("Background Color", "#FFFFFF")

box_size = st.slider("Size", min_value=5, max_value=20, value=10)

# Button to generate QR code
if st.button("Generate QR Code"):
    if data.strip() == "":
        st.warning("⚠️ Please enter some content.")
    else:
        # Create QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        # Convert image so Streamlit can display it
        img = img.convert("RGB")

        # Show image
        st.image(img, caption="Your QR Code", use_container_width=False)

        # Download option
        buf = BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 Download QR Code",
            data=byte_im,
            file_name="qr_code.png",
            mime="image/png"
        )

# Footer
st.markdown("---")
st.markdown("Made with [Streamlit](https://www.linkedin.com/company/108794161/admin/dashboard/)")