import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Dashboard Sampah Desa", layout="wide")

@st.cache_data

def load_data():
    df = pd.read_excel("Data Sampah.xlsx", usecols="A:Q")
    df.columns = df.columns.str.strip()
    return df

df_raw = load_data()

st.title("\U0001F4CA Dashboard Pengelolaan Sampah Desa")

with st.form("filter_form"):
    col1, col2, col3, col4 = st.columns(4)

    kabupaten_options = ["Semua"] + sorted(df_raw["KABUPATEN"].dropna().unique())
    kabupaten = col1.selectbox("📍 Kabupaten", kabupaten_options)

    if kabupaten != "Semua":
        kecamatan_options = ["Semua"] + sorted(df_raw[df_raw["KABUPATEN"] == kabupaten]["KECAMATAN"].dropna().unique())
    else:
        kecamatan_options = ["Semua"] + sorted(df_raw["KECAMATAN"].dropna().unique())
    kecamatan = col2.selectbox("🏙️ Kecamatan", kecamatan_options)

    if kecamatan != "Semua":
        desa_options = ["Semua"] + sorted(df_raw[df_raw["KECAMATAN"] == kecamatan]["DESA"].dropna().unique())
    else:
        desa_options = ["Semua"] + sorted(df_raw["DESA"].dropna().unique())
    desa = col3.selectbox("🏘️ Desa", desa_options)

    sistem_options = ["Semua"] + sorted(df_raw["Sistem Pengolahan Sampah"].dropna().unique())
    sistem = col4.selectbox("Sistem Pengolahan Sampah", sistem_options)

    submit = st.form_submit_button("Tampilkan Data")

if submit:
    df = df_raw.copy()
    if kabupaten != "Semua":
        df = df[df["KABUPATEN"] == kabupaten]
    if kecamatan != "Semua":
        df = df[df["KECAMATAN"] == kecamatan]
    if desa != "Semua":
        df = df[df["DESA"] == desa]
    if sistem != "Semua":
        df = df[df["Sistem Pengolahan Sampah"] == sistem]

    tab1, tab2, tab3 = st.tabs(["\U0001F4CC Ringkasan", "\U0001F4C8 Grafik", "\U0001F4C4 Data Mentah"])

    with tab1:
        st.subheader("\U0001F4CC Ringkasan per Kabupaten")

        st.markdown("### Sistem Pengelolaan Sampah")
        sistem_col = "Sistem Pengolahan Sampah"
        count_df = df.groupby("KABUPATEN")[sistem_col].value_counts().unstack(fill_value=0)
        count_df["Belum Terdata"] = df.groupby("KABUPATEN")[sistem_col].apply(lambda x: (x == "Belum terdata").sum())
        count_df = count_df.rename(columns={
            "Belum Ada": "Belum Ada Sistem",
            "Open Dumping": "Open Dumping",
            "TPS3R": "TPS3R",
            "Kombinasi": "Kombinasi"
        })
        expected_cols = [
            "Belum ada sistem pengolahan sampah di Desa (dibakar, ditimbun sendiri)",
            "Open Dumping", "TPS3R", "Kombinasi", "Belum Terdata"
        ]
        available_cols = [col for col in expected_cols if col in count_df.columns]
        count_df = count_df[available_cols]

        count_df.loc["Total"] = count_df.sum()

        st.markdown("#### Rekap Jumlah Keseluruhan")
        total_box = count_df.loc["Total"]
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        expected_labels = {
            "Belum ada sistem pengolahan sampah di Desa (dibakar, ditimbun sendiri)": "Belum Ada Sistem",
            "Open Dumping": "Open Dumping",
            "TPS3R": "TPS3R",
            "Kombinasi": "Kombinasi",
            "Belum Terdata": "Belum Terdata"
        }
        columns = st.columns(len(expected_labels))
        for i, (col_name, label) in enumerate(expected_labels.items()):
            if col_name in total_box:
                value = int(total_box[col_name])
                html_box = f"""
                <div style='
                    padding:5px;
                    border-radius:8px;
                    background:#00ff0080;
                    text-align:center;
                    font-size:24px;
                    transition: all 0.3s ease;
                    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                    cursor: default;' 
                    onmouseover="this.style.boxShadow='2px 4px 10px rgba(0,0,0,0.3)'" 
                    onmouseout="this.style.boxShadow='1px 1px 3px rgba(0,0,0,0.1)'">
                    <div style='font-weight:600;'>{label}</div>
                    <div style='font-size:30px; font-weight:bold'>{value}</div>
                </div>
                """
                columns[i].markdown(html_box, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)

        st.dataframe(count_df)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            count_df.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="Ringkasan Sistem", index=True)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Unduh Ringkasan Sistem Pengelolaan Sampah",
            data=excel_buffer,
            file_name="ringkasan_sistem_pengelolaan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("### TPS3R dan Bisnis Persampahan")
        bisnis_col = "Bisnis dalam bidang persampahan (sebagai contoh: Bank Sampah, Tabungan sampah)"
        bisnis_df = df[df["Sistem Pengolahan Sampah"] == "TPS3R"]
        if not bisnis_df.empty:
            bisnis_summary = bisnis_df.groupby("KABUPATEN")[bisnis_col].value_counts().unstack(fill_value=0)
            if not bisnis_summary.empty:
                bisnis_summary.loc["Total"] = bisnis_summary.sum()

                st.markdown("#### Rekap Keseluruhan")
                labels_bisnis = {
                    "Ada dan aktif": "Ada dan Aktif",
                    "Ada, namun tidak aktif": "Tidak Aktif",
                    "Ada dan aktif, Sedang dalam penyusunan rencana bisnis": "Aktif + Rencana",
                    "Ada, namun tidak aktif, Sedang dalam penyusunan rencana bisnis": "Tidak Aktif + Rencana",
                    "Sedang dalam penyusunan rencana bisnis": "Rencana Bisnis"
                }

                cols_bisnis = st.columns(len(labels_bisnis))
                for i, (col_name, label) in enumerate(labels_bisnis.items()):
                    if col_name in bisnis_summary.columns:
                        value = int(bisnis_summary.loc["Total", col_name])
                        html_box = f"""
                        <div style='
                            padding:10px;
                            border-radius:8px;
                            background:#00ff0080;
                            text-align:center;
                            font-size:24px;
                            transition: all 0.3s ease;
                            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                            cursor: default;' 
                            onmouseover="this.style.boxShadow='2px 4px 10px rgba(0,0,0,0.3)'" 
                            onmouseout="this.style.boxShadow='1px 1px 3px rgba(0,0,0,0.1)'">
                            <div style='font-weight:600;'>{label}</div>
                            <div style='font-size:30px; font-weight:bold'>{value}</div>
                        </div>
                        """
                        cols_bisnis[i].markdown(html_box, unsafe_allow_html=True)

                # Tambahkan jarak minimum ke tabel agar tidak terlalu jauh
                st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)

                # Tabel
                st.dataframe(bisnis_summary)

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    bisnis_summary.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="TPS3R dan Bisnis", index=True)
                excel_buffer.seek(0)

                st.download_button(
                    label="📥 Unduh Ringkasan TPS3R dan Bisnis",
                    data=excel_buffer,
                    file_name="ringkasan_TPS3R_bisnis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Tidak ada data bisnis persampahan untuk TPS3R di hasil filter ini.")
        else:
            st.info("Tidak ada data TPS3R dalam hasil filter ini.")



        st.markdown("### Pendapatan Asli Desa dan BUMDES")
        pad_col = "Pendapatan Asli Desa (PADes) dari bisnis persampahan"
        bumdes_col = "dikelola oleh BUMDes"
        if pad_col in df.columns and bumdes_col in df.columns:
            pad_df = df.groupby("KABUPATEN")[pad_col].value_counts().unstack(fill_value=0)
            bumdes_df = df.groupby("KABUPATEN")[bumdes_col].value_counts().unstack(fill_value=0)

            if not pad_df.empty and not bumdes_df.empty:
                pad_df.loc["Total"] = pad_df.sum()
                bumdes_df.loc["Total"] = bumdes_df.sum()

                st.markdown("#### Rekap Keseluruhan")

                labels_pad_bumdes = {
                    "PAD_Ya": "PAD - Ya",
                    "PAD_Tidak": "PAD - Tidak",
                    "BUMDes_Ya": "BUMDes - Ya",
                    "BUMDes_Tidak": "BUMDes - Tidak"
                }

                cols_pb = st.columns(len(labels_pad_bumdes))

                for i, (key, label) in enumerate(labels_pad_bumdes.items()):
                    if key == "PAD_Ya" and "Ya" in pad_df.columns:
                        value = int(pad_df.loc["Total", "Ya"])
                    elif key == "PAD_Tidak" and "Tidak" in pad_df.columns:
                        value = int(pad_df.loc["Total", "Tidak"])
                    elif key == "BUMDes_Ya" and "Ya" in bumdes_df.columns:
                        value = int(bumdes_df.loc["Total", "Ya"])
                    elif key == "BUMDes_Tidak" and "Tidak" in bumdes_df.columns:
                        value = int(bumdes_df.loc["Total", "Tidak"])
                    else:
                        continue

                    html_box = f"""
                    <div style='
                        padding:10px;
                        border-radius:8px;
                        background:#00ff0080;
                        text-align:center;
                        font-size:24px;
                        transition: all 0.3s ease;
                        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                        cursor: default;'
                        onmouseover="this.style.boxShadow='2px 4px 10px rgba(0,0,0,0.3)'"
                        onmouseout="this.style.boxShadow='1px 1px 3px rgba(0,0,0,0.1)'">
                        <div style='font-weight:600;'>{label}</div>
                        <div style='font-size:30px; font-weight:bold'>{value}</div>
                    </div>
                    """
                    cols_pb[i].markdown(html_box, unsafe_allow_html=True)

                # Jarak antar box dan tabel
                st.markdown("<div style='margin-top: -30px;'></div>", unsafe_allow_html=True)

                # Gabungan PAD dan BUMDes
                pad_bumdes_df = pad_df.merge(bumdes_df, left_index=True, right_index=True, suffixes=(" PAD", " BUMDes"))
                st.dataframe(pad_bumdes_df)


                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                    pad_bumdes_df.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="PADes dan BUMDES", index=True)
                excel_buffer.seek(0)

                st.download_button(
                    label="📥 Unduh Ringkasan PAD dan Bumdes",
                    data=excel_buffer,
                    file_name="ringkasan_PAD_Bumdes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.info("Tidak ada data PAD atau BUMDes pada hasil filter ini.")
        else:
            st.info("Kolom PAD atau BUMDes tidak ditemukan dalam data.")


    with tab2:
        st.subheader("\U0001F4C8 Grafik Interaktif")

        st.markdown("### Sistem Pengelolaan Sampah")
        fig = px.histogram(df, x="Sistem Pengolahan Sampah", color="Sistem Pengolahan Sampah",
                           title="Distribusi Sistem Pengolahan Sampah", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Bisnis Persampahan")
        fig2 = px.histogram(df, x=bisnis_col, color=bisnis_col,
                            title="Status Bisnis Persampahan", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### PAD dan BUMDes")
        fig3 = px.histogram(df, x=pad_col, color=pad_col,
                            title="Pendapatan Asli Desa (PADes)", text_auto=True)
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.histogram(df, x=bumdes_col, color=bumdes_col,
                            title="Dikelola oleh BUMDes", text_auto=True)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("### Rencana Pemdes Mengelola Sampah")
        fig5 = px.histogram(df, x="Rencana Pemdes mengolah Sampah", color="Rencana Pemdes mengolah Sampah",
                            title="Rencana Pemdes", text_auto=True)
        st.plotly_chart(fig5, use_container_width=True)

    with tab3:
        st.subheader("\U0001F4C4 Data Mentah")
        st.dataframe(df)
        # Tombol Download Excel
        to_excel = io.BytesIO()
        with pd.ExcelWriter(to_excel, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data Mentah")
        to_excel.seek(0)

        st.download_button(
            label="📥 Unduh Data dalam format Excel",
            data=to_excel,
            file_name="data_sampah_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Silakan pilih filter dan tekan tombol **Tampilkan Data** untuk melihat hasil.")
