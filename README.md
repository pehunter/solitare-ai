# Solitare AI
A Python AI Model that predicts the best move to make based on a given Solitare game state.
  
## Features
- 5x multiclass logistic regression models, all using Scikit-Learn, to predict the best move to make.
- Fully functional/playable solitare game
- Flask API that handles gameplay and reports game state & the predicted best move, running as a Gunicorn server.
- React/TS graphical web interface for the game and predicted move.
- Docker-compose file to launch app
  
## Structure
**data**: The .csv files used to train the model.  
**model**: Joblib'd dumps of the last trained model, along with their test accuracy.  
**game_server**: Contains game, ai trainer, and flask api to interface with these components.  
**site_src**: Contains source code/package info for web interface.  
**nginx**: Contains Dockerfile to setup NGINX file, along with config and production build of website  
  
## Todos
There are a few things to still be done for this project:
- Debug web interface
- Add back the 10 card (accidentally made 12 cards instead of 13 🫥)
- Add status on website to show AI training progress
  
### Lower-priority todos
- Figure out github pages
- Use AWS or equivalent to host project?
- Utilize issues instead of README.md todo list
