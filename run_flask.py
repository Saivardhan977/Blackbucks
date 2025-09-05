from app import app, init_db

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
