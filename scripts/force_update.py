from app import create_app
from app.services.game_service import GameService
from app.models.game import GameCache
from app.models.pick import MNFPrediction
from app import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_update_week10():
    app = create_app()
    with app.app_context():
        try:
            # Force update week 10 games
            logger.info("Forcing update of week 10 games...")
            games = GameService.update_week_games(week=10, force=True)
            
            # Get MNF game
            mnf_game = GameCache.query.filter_by(week=10, is_mnf=True).first()
            if mnf_game:
                logger.info(f"Found MNF game: {mnf_game.game_id}")
                logger.info(f"Status: {mnf_game.status}")
                logger.info(f"Score: {mnf_game.home_team} {mnf_game.home_score} - {mnf_game.away_team} {mnf_game.away_score}")
                logger.info(f"Is Final: {mnf_game.is_final()}")
                
                # Force the game to be final if it has scores
                if mnf_game.home_score is not None and mnf_game.away_score is not None:
                    logger.info("Setting game status to final...")
                    mnf_game.status = 'STATUS_FINAL'
                    db.session.add(mnf_game)
                    db.session.commit()
                
                # Update predictions
                actual_total = mnf_game.get_total_points()
                logger.info(f"Total points: {actual_total}")
                
                predictions = MNFPrediction.query.filter_by(week=10).all()
                for pred in predictions:
                    if pred.actual_total is None and actual_total is not None:
                        pred.calculate_difference(actual_total)
                        db.session.add(pred)
                        logger.info(f"Updated prediction for user {pred.user_id}: {pred.total_points} vs actual {actual_total}")
                
                db.session.commit()
                logger.info("Successfully updated all predictions")
            else:
                logger.error("No MNF game found for week 10")
                
        except Exception as e:
            logger.error(f"Error updating MNF data: {str(e)}")
            raise

if __name__ == '__main__':
    force_update_week10()
