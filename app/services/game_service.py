from datetime import datetime
from typing import List, Dict, Optional
from app.models.game import GameCache
from app.models.pick import Pick
from app.extensions import db
from app.services.espn_api import ESPNApiService
import logging
import json

logger = logging.getLogger(__name__)

class GameService:
    @staticmethod
    def normalize_team_name(team_name):
        """
        Normalize team names to handle different formats including abbreviations.
        E.g., 'PHI', 'Philadelphia', and 'Philadelphia Eagles' should all match.
        """
        if not team_name:
            return ''
            
        # Team abbreviation mapping
        abbrev_map = {
            'ARI': 'Arizona Cardinals',
            'ATL': 'Atlanta Falcons',
            'BAL': 'Baltimore Ravens',
            'BUF': 'Buffalo Bills',
            'CAR': 'Carolina Panthers',
            'CHI': 'Chicago Bears',
            'CIN': 'Cincinnati Bengals',
            'CLE': 'Cleveland Browns',
            'DAL': 'Dallas Cowboys',
            'DEN': 'Denver Broncos',
            'DET': 'Detroit Lions',
            'GB': 'Green Bay Packers',
            'HOU': 'Houston Texans',
            'IND': 'Indianapolis Colts',
            'JAX': 'Jacksonville Jaguars',
            'KC': 'Kansas City Chiefs',
            'LAC': 'Los Angeles Chargers',
            'LAR': 'Los Angeles Rams',
            'LV': 'Las Vegas Raiders',
            'MIA': 'Miami Dolphins',
            'MIN': 'Minnesota Vikings',
            'NE': 'New England Patriots',
            'NO': 'New Orleans Saints',
            'NYG': 'New York Giants',
            'NYJ': 'New York Jets',
            'PHI': 'Philadelphia Eagles',
            'PIT': 'Pittsburgh Steelers',
            'SEA': 'Seattle Seahawks',
            'SF': 'San Francisco 49ers',
            'TB': 'Tampa Bay Buccaneers',
            'TEN': 'Tennessee Titans',
            'WSH': 'Washington Commanders'
        }
        
        name = team_name.strip().upper()
        
        # Check if it's an abbreviation
        if name in abbrev_map:
            return abbrev_map[name].lower()
            
        # If not an abbreviation, normalize the full name
        name = team_name.strip()
        
        # Remove common words that might differ
        name = name.replace('Football Team', '').replace('Commanders', '').strip()
        
        # Remove city names
        city_prefixes = [
            'New York', 'Los Angeles', 'Las Vegas', 'San Francisco', 'Green Bay',
            'New England', 'Tampa Bay', 'Kansas City'
        ]
        for prefix in city_prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
                break
                
        return name.lower()

    @staticmethod
    def teams_match(team1, team2):
        """Check if two team names refer to the same team."""
        norm1 = GameService.normalize_team_name(team1)
        norm2 = GameService.normalize_team_name(team2)
        
        # Direct match after normalization
        if norm1 == norm2:
            return True
            
        # Check if one is contained within the other
        return norm1 in norm2 or norm2 in norm1

    @staticmethod
    def determine_pick_correctness(pick, game: GameCache):
        """
        Determine if a pick is correct based on the game scores.
        A pick is correct if the team they picked scored more points.
        """
        if not game.is_final():
            return None
            
        if game.home_score is None or game.away_score is None:
            logger.warning(f"Game {game.game_id} is final but missing scores: home={game.home_score}, away={game.away_score}")
            return None
            
        picked_team = pick.team_picked
        logger.info(f"Checking pick {pick.id}: picked '{picked_team}' vs home '{game.home_team}' or away '{game.away_team}'")
        
        # If they picked home team
        if GameService.teams_match(picked_team, game.home_team):
            logger.info(f"Matched home team {game.home_team}")
            return game.home_score > game.away_score
            
        # If they picked away team
        if GameService.teams_match(picked_team, game.away_team):
            logger.info(f"Matched away team {game.away_team}")
            return game.away_score > game.home_score
            
        logger.error(f"Pick {pick.id} has team '{picked_team}' that doesn't match home '{game.home_team}' or away '{game.away_team}'")
        return None

    @staticmethod
    def update_pick_results(game: GameCache):
        """Update pick results for a game that has finished."""
        if not game.is_final():
            logger.info(f"Skipping pick updates for game {game.game_id} - not final (status: {game.status})")
            return
            
        if game.home_score is None or game.away_score is None:
            logger.warning(f"Skipping pick updates for game {game.game_id} - missing scores")
            return
            
        # Get all picks for this game
        picks = Pick.query.filter_by(game_id=game.game_id).all()
        logger.info(f"Updating {len(picks)} picks for game {game.game_id}")
        logger.info(f"Final score: {game.home_team} {game.home_score} - {game.away_team} {game.away_score}")
        
        updates_made = False
        for pick in picks:
            old_value = pick.is_correct
            pick.is_correct = GameService.determine_pick_correctness(pick, game)
            
            if old_value != pick.is_correct:
                updates_made = True
                logger.info(f"Updated pick {pick.id} for user {pick.user_id}: picked {pick.team_picked}, " +
                          f"score: {game.home_team}({game.home_score})-{game.away_team}({game.away_score}), " +
                          f"correct: {pick.is_correct}")
        
        if updates_made:
            try:
                db.session.commit()
                logger.info(f"Successfully updated pick results for game {game.game_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating pick results: {str(e)}")
                raise
        else:
            logger.info(f"No pick updates needed for game {game.game_id}")

    @staticmethod
    def update_all_pick_results():
        """
        Force update all pick results for finished games
        """
        try:
            # Get all games that might be final
            all_games = GameCache.query.all()
            
            # Debug log all games
            for game in all_games:
                logger.info(f"Game {game.game_id}: status={game.status}, " +
                          f"score={game.home_team}({game.home_score})-{game.away_team}({game.away_score})")
            
            finished_games = [game for game in all_games if game.is_final()]
            logger.info(f"Found {len(finished_games)} finished games to update picks for")
            
            updates_made = 0
            # Process each finished game
            for game in finished_games:
                if game.home_score is None or game.away_score is None:
                    logger.warning(f"Skipping game {game.game_id} - missing scores")
                    continue
                    
                logger.info(f"Processing finished game {game.game_id}")
                logger.info(f"Final score: {game.home_team} {game.home_score} - {game.away_team} {game.away_score}")
                
                # Get all picks for this game
                picks = Pick.query.filter_by(game_id=game.game_id).all()
                logger.info(f"Found {len(picks)} picks for game {game.game_id}")
                
                for pick in picks:
                    old_value = pick.is_correct
                    pick.is_correct = GameService.determine_pick_correctness(pick, game)
                    
                    if old_value != pick.is_correct:
                        updates_made += 1
                        logger.info(f"Updated pick {pick.id} for user {pick.user_id}: " +
                                  f"picked {pick.team_picked}, " +
                                  f"score: {game.home_team}({game.home_score})-{game.away_team}({game.away_score}), " +
                                  f"correct: {pick.is_correct}")
            
            if updates_made > 0:
                db.session.commit()
                logger.info(f"Successfully updated {updates_made} pick results")
            else:
                logger.info("No pick updates needed")
                
            return updates_made
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating pick results: {str(e)}")
            raise

    @staticmethod
    def update_week_games(week: Optional[int] = None, force: bool = False) -> List[Dict]:
        """
        Update the game cache for a specific week or current week
        
        Args:
            week: Week number to update. If None, uses current week
            force: If True, forces update even if cache exists
        """
        try:
            # Validate week number
            if week is not None and (week < 1 or week > 18):
                logger.warning(f"Invalid week number: {week}")
                return []

            # Get current NFL week if not specified
            if week is None:
                current = ESPNApiService.get_current_nfl_week()
                week = current['week']
                season_type = current['season_type']
                year = current['year']
                logger.info(f"Current NFL week: {week}, season_type: {season_type}, year: {year}")
            else:
                season_type = 2  # Regular season
                year = datetime.now().year
            
            # Check cache first
            if not force:
                cached_games = GameCache.query.filter_by(
                    week=week,
                    season_type=season_type,
                    year=year
                ).all()
                
                if cached_games:
                    logger.info(f"Found {len(cached_games)} cached games for week {week}")
                    # Convert to dictionary format
                    return [json.loads(game.data) for game in cached_games]
            
            # Fetch fresh data from ESPN
            logger.info(f"Fetching fresh game data from ESPN for week {week}")
            games = ESPNApiService.get_week_games(week, season_type, year)
            
            if not games:
                logger.warning(f"No games found for week {week}. This might be the offseason.")
                return []
            
            # Update cache
            try:
                GameService.update_game_cache(games)
                
                # Update pick results if game is final
                for game in games:
                    existing_game = GameCache.query.filter_by(game_id=game['game_id']).first()
                    if existing_game and existing_game.is_final():
                        GameService.update_pick_results(existing_game)
                    
                logger.info(f"Successfully updated game cache for week {week}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating game cache: {str(e)}")
                raise
                
            return games
            
        except Exception as e:
            logger.error(f"Error in update_week_games: {str(e)}")
            return []

    @staticmethod
    def update_game_cache(games):
        """Update game cache with new game data."""
        try:
            logger.info(f"Updating {len(games)} games in cache")
            for game_data in games:
                # Try to find existing game
                existing_game = GameCache.query.filter_by(game_id=game_data['game_id']).first()
                
                # Get winner if game is final
                winning_team = game_data.get('winning_team')
                game_status = game_data.get('status', '')
                
                logger.info(f"Processing game {game_data['game_id']}: {game_data['away_team']['display_name']} @ {game_data['home_team']['display_name']}")
                logger.info(f"Status: {game_status}, Winner: {winning_team}")
                
                if existing_game:
                    # Log current state
                    logger.info(f"Existing game found - Current state: status={existing_game.status}, winner={existing_game.winning_team}")
                    
                    # Update existing game
                    existing_game.data = json.dumps(game_data)
                    existing_game.status = game_status
                    existing_game.winning_team = winning_team
                    existing_game.home_team = game_data['home_team']['display_name']
                    existing_game.away_team = game_data['away_team']['display_name']
                    existing_game.home_team_abbrev = game_data['home_team']['abbreviation']
                    existing_game.away_team_abbrev = game_data['away_team']['abbreviation']
                    existing_game.home_score = game_data['home_team']['score']
                    existing_game.away_score = game_data['away_team']['score']
                    existing_game.last_updated = datetime.utcnow()
                    
                    # Update picks if game just finished
                    if existing_game.is_final():
                        logger.info(f"Updating picks for finished game {game_data['game_id']}")
                        GameService.update_pick_results(existing_game)
                else:
                    logger.info(f"Creating new game record for {game_data['game_id']}")
                    # Create new game
                    new_game = GameCache(
                        week=game_data['week']['number'],  # Extract the week number from the week object
                        season_type=game_data['season_type'],
                        year=game_data['year'],
                        game_id=game_data['game_id'],
                        data=json.dumps(game_data),
                        status=game_status,
                        winning_team=winning_team,
                        home_team=game_data['home_team']['display_name'],
                        away_team=game_data['away_team']['display_name'],
                        home_team_abbrev=game_data['home_team']['abbreviation'],
                        away_team_abbrev=game_data['away_team']['abbreviation'],
                        home_score=game_data['home_team']['score'],
                        away_score=game_data['away_team']['score'],
                        start_time=datetime.fromisoformat(game_data['date'].replace('Z', '+00:00')),
                        is_mnf=game_data.get('is_mnf', False),
                        venue_name=game_data['venue']['name'],
                        venue_city=game_data['venue']['city'],
                        venue_state=game_data['venue']['state']
                    )
                    db.session.add(new_game)
                    
                    # Update picks if game is final
                    if new_game.is_final():
                        logger.info(f"Updating picks for new finished game {game_data['game_id']}")
                        db.session.flush()  # Ensure new_game has an ID
                        GameService.update_pick_results(new_game)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating game cache: {str(e)}")
            raise

    @staticmethod
    def get_week_games(week: Optional[int] = None, force_update: bool = False) -> List[Dict]:
        """
        Get all games for a specific week, using cache when available
        
        Args:
            week: Week number to get games for. If None, uses current week
            force_update: If True, forces a fresh fetch from ESPN
        """
        return GameService.update_week_games(week, force_update)

    @staticmethod
    def get_current_nfl_week() -> Dict:
        """Get the current NFL week information"""
        return ESPNApiService.get_current_nfl_week()

    @staticmethod
    def get_mnf_game(week: Optional[int] = None) -> Optional[Dict]:
        """Get the Monday Night Football game for a specific week"""
        games = GameService.get_week_games(week)
        for game in games:
            if game.get('is_mnf'):
                return game
        return None
