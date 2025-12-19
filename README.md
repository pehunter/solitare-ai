# Solitare AI
A Python AI Model that predicts the best move to make based on a given Solitare game state.

This project has the following:
- 5x multiclass logistic regression models, all using Scikit-Learn, to predict the best move to make.
- Fully functional/playable solitare game
- Flask API that handles gameplay and reports game state & the predicted best move, running as a Gunicorn server.
- React/TS graphical web interface for the game and predicted move.

## Todos
There are a few things to still be done for this project:
- Debug web interface
- Create nginx container to serve website and interface with backend gunicorn container
- Add back the 10 card (accidentally made 12 cards instead of 13 🫥)

### Lower-priority todos
- Figure out github pages
- Use AWS or equivalent to host project?
- Utilize issues instead of README.md todo list
