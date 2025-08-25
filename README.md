# P&C Loss Ratio Dashboard

An interactive dashboard for visualizing P&C insurance loss ratio trends, built with Python and Dash.

**➡️ Live Demo: [loss-ratio-dashboard.onrender.com](https://loss-ratio-dashboard.onrender.com/)**

![Dashboard Screenshot](https://placehold.co/800x450/f5f1e9/3C2A21?text=Dashboard+Preview)

---

### About This Project

I built this dashboard to make a core actuarial concept—the loss ratio—more tangible and interactive. The goal was to create a tool that could clearly show the difference between initial, **"as-reported"** loss estimates and the more mature, **"developed ultimate"** figures that actuaries work towards.

It's a simple BI tool designed to let users filter by business line and region, track trends over time, and see the real financial impact of loss development in a clean, visual way.

### Tech Stack

- **Python** | **Dash** | **Plotly** for the interactive front-end
- **Pandas** for data wrangling
- **Gunicorn** & **Render** for deployment

### Running Locally

To get this running on your own machine:

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/priyam0k/loss-ratio-dashboard.git](https://github.com/priyam0k/loss-ratio-dashboard.git)
    cd loss-ratio-dashboard
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate the data:**
    The dashboard runs on a synthetic dataset. This script creates it.
    ```bash
    python create_data.py
    ```

4.  **Run the app:**
    ```bash
    python app.py
    ```
    Then head over to `http://127.0.0.1:8050/` in your browser.

### How It Works

-   **`create_data.py`**: This script generates a clean, synthetic dataset based on a simple star schema. It simulates realistic trends, seasonality, and—most importantly—the loss development process by creating both an initial `incurred_loss` and a final `developed_loss`.
-   **`app.py`**: This is the Dash application. It loads the data, lays out the UI, and uses a single callback to handle all the filtering logic. When you change a filter, the callback slices the Pandas DataFrame and redraws the Plotly charts.

That's it! Feel free to open an issue if you have any questions.
