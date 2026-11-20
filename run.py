from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 70)
    print("POCKET MECHANIC: Predictive Motorcycle Diagnostics Platform")
    print("Local Server Launching on http://127.0.0.1:5001")
    print("=" * 70)
    app.run(host='127.0.0.1', port=5001, debug=True)
