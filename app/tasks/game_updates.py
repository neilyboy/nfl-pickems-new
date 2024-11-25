from flask import current_app
from app.services.espn_api import ESPNApiService
from app.models import GameCache, MNFPrediction
from app import db
import json
from datetime import datetime, timedelta
import time
import threading
import logging
from dateutil import tz

logger = logging.getLogger(__name__)

def update_mnf_games():
    """Background task to update MNF games automatically."""
    with current_app.app_context():
        try:
            # Get current week info
            week_info = ESPNApiService.get_current_nfl_week()
            week = week_info.get('week')
            season_type = week_info.get('season_type')
            year = week_info.get('year')
            
            logger.info(f"Checking for MNF updates - Week {week}, Season Type {season_type}, Year {year}")
            
            # Get all games for the week
            games = ESPNApiService.get_week_games(week=week, season_type=season_type, year=year)
            
            # Find MNF game
            mnf_game = None
            for game_data in games:
                if game_data.get('is_mnf'):
                    mnf_game = game_data
                    break
            
            if not mnf_game:
                logger.info("No MNF game found for current week")
                return
                
            logger.info(f"Found MNF game: {mnf_game.get('home_team', {}).get('display_name')} vs {mnf_game.get('away_team', {}).get('display_name')}")
            
            # Update game in cache
            game = GameCache.query.filter_by(game_id=mnf_game.get('game_id')).first()
            if not game:
                game = GameCache(
                    game_id=mnf_game.get('game_id'),
                    week=week,
                    data=json.dumps(mnf_game),
                    home_team=mnf_game.get('home_team', {}).get('display_name'),
                    away_team=mnf_game.get('away_team', {}).get('display_name'),
                    home_team_abbrev=mnf_game.get('home_team', {}).get('abbreviation'),
                    away_team_abbrev=mnf_game.get('away_team', {}).get('abbreviation'),
                    home_score=mnf_game.get('home_team', {}).get('score'),
                    away_score=mnf_game.get('away_team', {}).get('score'),
                    status=mnf_game.get('status'),
                    venue_name=mnf_game.get('venue', {}).get('name'),
                    venue_city=mnf_game.get('venue', {}).get('city'),
                    venue_state=mnf_game.get('venue', {}).get('state'),
                    start_time=mnf_game.get('date'),
                    is_mnf=True
                )
            else:
                game.data = json.dumps(mnf_game)
                game.home_score = mnf_game.get('home_team', {}).get('score')
                game.away_score = mnf_game.get('away_team', {}).get('score')
                game.status = mnf_game.get('status')
            
            try:
                db.session.add(game)
                db.session.commit()
                logger.info(f"Updated game {game.game_id} in cache")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating game in cache: {str(e)}")
                return
            
            # If game is final, update predictions
            if game.status in ['STATUS_FINAL', 'STATUS_FINAL_OVERTIME']:
                actual_total = game.get_total_points()
                if actual_total:
                    logger.info(f"Game is final with total points: {actual_total}")
                    predictions = MNFPrediction.query.filter_by(week=week).all()
                    for pred in predictions:
                        try:
                            if pred.actual_total is None:
                                pred.calculate_difference(actual_total)
                                db.session.add(pred)
                                logger.info(f"Updated prediction for user {pred.user_id}: {pred.total_points} vs actual {actual_total}")
                        except Exception as e:
                            logger.error(f"Error updating prediction {pred.id}: {str(e)}")
                            continue
                    
                    try:
                        db.session.commit()
                        logger.info("Successfully updated all predictions")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error saving prediction updates: {str(e)}")
            else:
                logger.info(f"Game status is {game.status} - not updating predictions yet")
                
        except Exception as e:
            logger.error(f"Error in update_mnf_games: {str(e)}")

def init_game_updates(app):
    """Initialize the game updates background task with app context."""
    def update_loop():
        with app.app_context():
            while True:
                try:
                    update_mnf_games()
                except Exception as e:
                    logger.error(f"Error in update loop: {str(e)}")
                # Wait 5 minutes before next update
                time.sleep(300)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    logger.info("Started MNF game update thread")

def start_game_updates():
    """
    Deprecated: Use init_game_updates(app) instead.
    This function remains for backward compatibility.
    """
    logger.warning("start_game_updates() is deprecated. Use init_game_updates(app) instead.")
