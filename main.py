from Algo_Trading import app, create_app, create_database

app= create_app()

if __name__ == '__main__':
    # create_database(app)
    app.run(debug=True)