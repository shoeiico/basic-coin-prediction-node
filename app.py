import json
import os
from flask import Flask, Response
from model import download_data, format_data, train_model, get_inference
from config import model_file_path, TOKEN, TIMEFRAME, TRAINING_DAYS, REGION, DATA_PROVIDER

app = Flask(__name__)

def update_data():
    print("Starting data update process...")
    # Clear existing data to force refresh
    data_dir = os.path.join(os.getcwd(), "data", "binance")
    price_data_file = os.path.join(os.getcwd(), "data", "price_data.csv")
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            os.remove(os.path.join(data_dir, f))
    if os.path.exists(price_data_file):
        os.remove(price_data_file)
    
    files_btc = download_data("BTC", TRAINING_DAYS, REGION, DATA_PROVIDER)
    files_eth = download_data("ETH", TRAINING_DAYS, REGION, DATA_PROVIDER)
    if not files_btc or not files_eth:
        print("No data files downloaded. Skipping format_data and training.")
        return
    format_data(files_btc, files_eth, DATA_PROVIDER)
    train_model(TIMEFRAME)

@app.route("/inference/<string:token>")
def generate_inference(token):
    if not token or token.upper() != TOKEN:
        error_msg = "Token is required" if not token else f"Token {token} not supported, expected {TOKEN}"
        return Response(json.dumps({"error": error_msg}), status=400, mimetype='application/json')
    try:
        if not os.path.exists(model_file_path):
            raise FileNotFoundError("Model file not found. Please run update first to train the model.")
        inference = get_inference(token.upper(), TIMEFRAME, REGION, DATA_PROVIDER)
        return Response(str(inference), status=200, mimetype='text/plain')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

@app.route("/update")
def update():
    try:
        update_data()
        return "0"
    except Exception as e:
        print(f"Update failed: {str(e)}")
        return "1"

if __name__ == "__main__":
    update_data()
    app.run(host="0.0.0.0", port=8000)
