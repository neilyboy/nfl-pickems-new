from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.game_service import GameService
import logging

logger = logging.getLogger(__name__)

def init_scheduler(app):
    """Initialize the scheduler with the app context"""
    scheduler = BackgroundScheduler()
    
    # Update games every 2 minutes during game time (Thursday, Sunday, Monday nights)
    def update_games():
        with app.app_context():
            try:
                GameService.update_week_games(force=True)
                logger.info("Successfully updated game data")
            except Exception as e:
                logger.error(f"Error updating game data: {str(e)}")

    # Thursday Night Football updates (8 PM - 12 AM ET)
    scheduler.add_job(
        update_games,
        CronTrigger(day_of_week='thu', hour='20-23', minute='*/2', timezone='US/Eastern')
    )

    # Sunday updates (1 PM - 12 AM ET)
    scheduler.add_job(
        update_games,
        CronTrigger(day_of_week='sun', hour='13-23', minute='*/2', timezone='US/Eastern')
    )

    # Monday Night Football updates (8 PM - 12 AM ET)
    scheduler.add_job(
        update_games,
        CronTrigger(day_of_week='mon', hour='20-23', minute='*/2', timezone='US/Eastern')
    )

    # Daily update at 4 AM ET to get final scores and new odds
    scheduler.add_job(
        update_games,
        CronTrigger(hour=4, timezone='US/Eastern')
    )

    scheduler.start()
    return scheduler
