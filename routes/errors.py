from app import app

@app.errorhandler(404)
def error_404(e):
    return {
        'Message': 'Page Not Found !'
    },404

@app.errorhandler(500)
def error_404(e):
    return {
        'Message': 'Oop! Internal Server Error '
    },500
